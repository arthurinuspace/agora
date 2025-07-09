"""
Database migration system for Agora Slack app.
Handles schema updates and data migrations safely.
"""

import os
import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, Text, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from config import Config

logger = logging.getLogger(__name__)

class Migration:
    """Base class for database migrations."""
    
    def __init__(self, version: str, description: str):
        self.version = version
        self.description = description
        self.applied_at = None
    
    def up(self, engine, metadata):
        """Apply the migration."""
        raise NotImplementedError("Subclasses must implement up() method")
    
    def down(self, engine, metadata):
        """Rollback the migration."""
        raise NotImplementedError("Subclasses must implement down() method")
    
    def __str__(self):
        return f"Migration {self.version}: {self.description}"

class MigrationManager:
    """Manages database migrations."""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or Config.DATABASE_URL
        self.engine = create_engine(self.database_url)
        self.metadata = MetaData()
        self.migrations = []
        self._ensure_migration_table()
    
    def _ensure_migration_table(self):
        """Create migrations table if it doesn't exist."""
        try:
            # Create migration tracking table
            migrations_table = Table(
                'schema_migrations',
                self.metadata,
                Column('id', Integer, primary_key=True),
                Column('version', String(50), unique=True, nullable=False),
                Column('description', Text, nullable=False),
                Column('applied_at', DateTime, nullable=False),
                Column('checksum', String(64), nullable=True)
            )
            
            # Create table if it doesn't exist
            if not inspect(self.engine).has_table('schema_migrations'):
                migrations_table.create(self.engine)
                logger.info("Created schema_migrations table")
        
        except Exception as e:
            logger.error(f"Error creating migrations table: {e}")
            raise
    
    def register_migration(self, migration: Migration):
        """Register a migration."""
        self.migrations.append(migration)
        self.migrations.sort(key=lambda m: m.version)
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration versions."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT version FROM schema_migrations ORDER BY version"))
                return [row[0] for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Error getting applied migrations: {e}")
            return []
    
    def get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations."""
        applied = set(self.get_applied_migrations())
        return [m for m in self.migrations if m.version not in applied]
    
    def apply_migration(self, migration: Migration) -> bool:
        """Apply a single migration."""
        try:
            logger.info(f"Applying migration: {migration}")
            
            with self.engine.begin() as conn:
                # Apply the migration
                migration.up(self.engine, self.metadata)
                
                # Record the migration
                conn.execute(text("""
                    INSERT INTO schema_migrations (version, description, applied_at)
                    VALUES (:version, :description, :applied_at)
                """), {
                    'version': migration.version,
                    'description': migration.description,
                    'applied_at': datetime.now()
                })
                
                logger.info(f"Successfully applied migration: {migration.version}")
                return True
                
        except Exception as e:
            logger.error(f"Error applying migration {migration.version}: {e}")
            return False
    
    def rollback_migration(self, migration: Migration) -> bool:
        """Rollback a single migration."""
        try:
            logger.info(f"Rolling back migration: {migration}")
            
            with self.engine.begin() as conn:
                # Rollback the migration
                migration.down(self.engine, self.metadata)
                
                # Remove migration record
                conn.execute(text("""
                    DELETE FROM schema_migrations WHERE version = :version
                """), {'version': migration.version})
                
                logger.info(f"Successfully rolled back migration: {migration.version}")
                return True
                
        except Exception as e:
            logger.error(f"Error rolling back migration {migration.version}: {e}")
            return False
    
    def migrate_up(self, target_version: str = None) -> bool:
        """Apply all pending migrations up to target version."""
        pending = self.get_pending_migrations()
        
        if target_version:
            pending = [m for m in pending if m.version <= target_version]
        
        if not pending:
            logger.info("No pending migrations to apply")
            return True
        
        logger.info(f"Applying {len(pending)} migrations...")
        
        for migration in pending:
            if not self.apply_migration(migration):
                logger.error(f"Migration failed at version {migration.version}")
                return False
        
        logger.info("All migrations applied successfully")
        return True
    
    def migrate_down(self, target_version: str) -> bool:
        """Rollback migrations down to target version."""
        applied = self.get_applied_migrations()
        applied.reverse()  # Rollback in reverse order
        
        migrations_to_rollback = []
        for version in applied:
            if version > target_version:
                migration = next((m for m in self.migrations if m.version == version), None)
                if migration:
                    migrations_to_rollback.append(migration)
        
        if not migrations_to_rollback:
            logger.info("No migrations to rollback")
            return True
        
        logger.info(f"Rolling back {len(migrations_to_rollback)} migrations...")
        
        for migration in migrations_to_rollback:
            if not self.rollback_migration(migration):
                logger.error(f"Rollback failed at version {migration.version}")
                return False
        
        logger.info("All rollbacks completed successfully")
        return True
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status."""
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()
        
        return {
            'applied_count': len(applied),
            'pending_count': len(pending),
            'applied_migrations': applied,
            'pending_migrations': [m.version for m in pending],
            'last_applied': applied[-1] if applied else None
        }

# Define specific migrations
class InitialMigration(Migration):
    """Initial database schema migration."""
    
    def __init__(self):
        super().__init__("001", "Initial database schema")
    
    def up(self, engine, metadata):
        """Create initial tables."""
        from models import Base
        Base.metadata.create_all(engine)
    
    def down(self, engine, metadata):
        """Drop all tables."""
        from models import Base
        Base.metadata.drop_all(engine)

class AddIndexesMigration(Migration):
    """Add performance indexes."""
    
    def __init__(self):
        super().__init__("002", "Add performance indexes")
    
    def up(self, engine, metadata):
        """Add indexes for better performance."""
        with engine.connect() as conn:
            # Add indexes that might be missing
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_polls_team_status ON polls(team_id, status)",
                "CREATE INDEX IF NOT EXISTS idx_polls_channel_status ON polls(channel_id, status)",
                "CREATE INDEX IF NOT EXISTS idx_polls_creator_created ON polls(creator_id, created_at)",
                "CREATE INDEX IF NOT EXISTS idx_poll_options_poll_order ON poll_options(poll_id, order_index)",
                "CREATE INDEX IF NOT EXISTS idx_voted_users_poll_user ON voted_users(poll_id, user_id)",
                "CREATE INDEX IF NOT EXISTS idx_user_votes_poll_option ON user_votes(poll_id, option_id)",
                "CREATE INDEX IF NOT EXISTS idx_user_roles_user_team ON user_roles(user_id, team_id)",
                "CREATE INDEX IF NOT EXISTS idx_notifications_user_sent ON notifications(user_id, sent_at)",
                "CREATE INDEX IF NOT EXISTS idx_poll_shares_poll_channel ON poll_shares(poll_id, channel_id)"
            ]
            
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                    conn.commit()
                except Exception as e:
                    logger.warning(f"Index creation failed (may already exist): {e}")
    
    def down(self, engine, metadata):
        """Remove added indexes."""
        with engine.connect() as conn:
            # Drop indexes
            indexes_to_drop = [
                "DROP INDEX IF EXISTS idx_polls_team_status",
                "DROP INDEX IF EXISTS idx_polls_channel_status",
                "DROP INDEX IF EXISTS idx_polls_creator_created",
                "DROP INDEX IF EXISTS idx_poll_options_poll_order",
                "DROP INDEX IF EXISTS idx_voted_users_poll_user",
                "DROP INDEX IF EXISTS idx_user_votes_poll_option",
                "DROP INDEX IF EXISTS idx_user_roles_user_team",
                "DROP INDEX IF EXISTS idx_notifications_user_sent",
                "DROP INDEX IF EXISTS idx_poll_shares_poll_channel"
            ]
            
            for drop_sql in indexes_to_drop:
                try:
                    conn.execute(text(drop_sql))
                    conn.commit()
                except Exception as e:
                    logger.warning(f"Index drop failed: {e}")

class AddAnalyticsTablesMigration(Migration):
    """Add analytics tables for better reporting."""
    
    def __init__(self):
        super().__init__("003", "Add analytics tables")
    
    def up(self, engine, metadata):
        """Add analytics tables."""
        with engine.connect() as conn:
            # Check if tables already exist
            inspector = inspect(engine)
            
            if not inspector.has_table('poll_analytics'):
                conn.execute(text("""
                    CREATE TABLE poll_analytics (
                        id INTEGER PRIMARY KEY,
                        poll_id INTEGER NOT NULL,
                        total_votes INTEGER DEFAULT 0,
                        unique_voters INTEGER DEFAULT 0,
                        participation_rate REAL DEFAULT 0.0,
                        avg_response_time REAL DEFAULT 0.0,
                        peak_voting_hour INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (poll_id) REFERENCES polls(id)
                    )
                """))
                conn.commit()
            
            if not inspector.has_table('vote_activity'):
                conn.execute(text("""
                    CREATE TABLE vote_activity (
                        id INTEGER PRIMARY KEY,
                        poll_id INTEGER NOT NULL,
                        hour INTEGER NOT NULL,
                        vote_count INTEGER DEFAULT 0,
                        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (poll_id) REFERENCES polls(id)
                    )
                """))
                conn.commit()
    
    def down(self, engine, metadata):
        """Remove analytics tables."""
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS vote_activity"))
            conn.execute(text("DROP TABLE IF EXISTS poll_analytics"))
            conn.commit()

class AddNotificationSystemMigration(Migration):
    """Add notification system tables."""
    
    def __init__(self):
        super().__init__("004", "Add notification system")
    
    def up(self, engine, metadata):
        """Add notification tables."""
        with engine.connect() as conn:
            inspector = inspect(engine)
            
            if not inspector.has_table('notification_settings'):
                conn.execute(text("""
                    CREATE TABLE notification_settings (
                        id INTEGER PRIMARY KEY,
                        user_id VARCHAR(255) NOT NULL,
                        team_id VARCHAR(255) NOT NULL,
                        poll_created BOOLEAN DEFAULT 1,
                        poll_ended BOOLEAN DEFAULT 1,
                        vote_milestone BOOLEAN DEFAULT 1,
                        close_race BOOLEAN DEFAULT 1,
                        role_changed BOOLEAN DEFAULT 1,
                        daily_summary BOOLEAN DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.commit()
            
            if not inspector.has_table('notifications'):
                conn.execute(text("""
                    CREATE TABLE notifications (
                        id INTEGER PRIMARY KEY,
                        user_id VARCHAR(255) NOT NULL,
                        team_id VARCHAR(255) NOT NULL,
                        poll_id INTEGER,
                        notification_type VARCHAR(50) NOT NULL,
                        title VARCHAR(255) NOT NULL,
                        message TEXT NOT NULL,
                        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        read_at TIMESTAMP,
                        FOREIGN KEY (poll_id) REFERENCES polls(id)
                    )
                """))
                conn.commit()
    
    def down(self, engine, metadata):
        """Remove notification tables."""
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS notifications"))
            conn.execute(text("DROP TABLE IF EXISTS notification_settings"))
            conn.commit()

class AddCrossChannelSharingMigration(Migration):
    """Add cross-channel sharing support."""
    
    def __init__(self):
        super().__init__("005", "Add cross-channel sharing")
    
    def up(self, engine, metadata):
        """Add cross-channel sharing tables."""
        with engine.connect() as conn:
            inspector = inspect(engine)
            
            if not inspector.has_table('poll_shares'):
                conn.execute(text("""
                    CREATE TABLE poll_shares (
                        id INTEGER PRIMARY KEY,
                        poll_id INTEGER NOT NULL,
                        channel_id VARCHAR(255) NOT NULL,
                        message_ts VARCHAR(255),
                        shared_by VARCHAR(255) NOT NULL,
                        shared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1,
                        FOREIGN KEY (poll_id) REFERENCES polls(id)
                    )
                """))
                conn.commit()
            
            if not inspector.has_table('cross_channel_views'):
                conn.execute(text("""
                    CREATE TABLE cross_channel_views (
                        id INTEGER PRIMARY KEY,
                        user_id VARCHAR(255) NOT NULL,
                        team_id VARCHAR(255) NOT NULL,
                        poll_id INTEGER NOT NULL,
                        viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (poll_id) REFERENCES polls(id)
                    )
                """))
                conn.commit()
    
    def down(self, engine, metadata):
        """Remove cross-channel sharing tables."""
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS cross_channel_views"))
            conn.execute(text("DROP TABLE IF EXISTS poll_shares"))
            conn.commit()

# Migration registry
def get_migration_manager() -> MigrationManager:
    """Get configured migration manager with all migrations."""
    manager = MigrationManager()
    
    # Register all migrations
    manager.register_migration(InitialMigration())
    manager.register_migration(AddIndexesMigration())
    manager.register_migration(AddAnalyticsTablesMigration())
    manager.register_migration(AddNotificationSystemMigration())
    manager.register_migration(AddCrossChannelSharingMigration())
    
    return manager

# Command line interface
def main():
    """Command line interface for migrations."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database Migration Tool")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show migration status')
    
    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Apply migrations')
    migrate_parser.add_argument('--target', help='Target version')
    
    # Rollback command
    rollback_parser = subparsers.add_parser('rollback', help='Rollback migrations')
    rollback_parser.add_argument('target', help='Target version')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create new migration')
    create_parser.add_argument('description', help='Migration description')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = get_migration_manager()
    
    if args.command == 'status':
        status = manager.get_migration_status()
        print(f"Applied migrations: {status['applied_count']}")
        print(f"Pending migrations: {status['pending_count']}")
        print(f"Last applied: {status['last_applied']}")
        
        if status['pending_migrations']:
            print("\nPending migrations:")
            for version in status['pending_migrations']:
                print(f"  {version}")
    
    elif args.command == 'migrate':
        success = manager.migrate_up(args.target)
        if success:
            print("Migrations applied successfully")
        else:
            print("Migration failed")
            exit(1)
    
    elif args.command == 'rollback':
        success = manager.migrate_down(args.target)
        if success:
            print("Rollback completed successfully")
        else:
            print("Rollback failed")
            exit(1)
    
    elif args.command == 'create':
        # Generate next version number
        applied = manager.get_applied_migrations()
        if applied:
            last_version = max(applied)
            next_version = f"{int(last_version) + 1:03d}"
        else:
            next_version = "001"
        
        migration_template = f'''"""
{args.description}
"""

from migrations import Migration

class CustomMigration(Migration):
    def __init__(self):
        super().__init__("{next_version}", "{args.description}")
    
    def up(self, engine, metadata):
        """Apply the migration."""
        # TODO: Implement migration logic
        pass
    
    def down(self, engine, metadata):
        """Rollback the migration."""
        # TODO: Implement rollback logic
        pass
'''
        
        filename = f"migration_{next_version}_{args.description.lower().replace(' ', '_')}.py"
        with open(filename, 'w') as f:
            f.write(migration_template)
        
        print(f"Created migration file: {filename}")

if __name__ == "__main__":
    main()