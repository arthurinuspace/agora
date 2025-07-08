"""
Poll templates system for Agora Slack app.
Provides predefined templates for common voting scenarios.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class TemplateCategory(Enum):
    """Template categories for organization."""
    DECISION_MAKING = "decision_making"
    TEAM_FEEDBACK = "team_feedback"
    PLANNING = "planning"
    SOCIAL = "social"
    MEETING = "meeting"
    PRODUCT = "product"

@dataclass
class PollTemplate:
    """Poll template data structure."""
    id: str
    name: str
    description: str
    category: TemplateCategory
    question: str
    options: List[str]
    vote_type: str  # "single" or "multiple"
    suggested_duration: int  # minutes
    tags: List[str]
    created_at: datetime
    usage_count: int = 0

class TemplateManager:
    """Manages poll templates."""
    
    def __init__(self):
        self.templates: Dict[str, PollTemplate] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default poll templates."""
        default_templates = [
            # Decision Making Templates
            PollTemplate(
                id="yes-no-decision",
                name="Yes/No Decision",
                description="Simple binary decision for team consensus",
                category=TemplateCategory.DECISION_MAKING,
                question="Should we proceed with this proposal?",
                options=["✅ Yes", "❌ No"],
                vote_type="single",
                suggested_duration=60,
                tags=["decision", "binary", "consensus"],
                created_at=datetime.now()
            ),
            
            PollTemplate(
                id="priority-ranking",
                name="Priority Ranking",
                description="Rank items by priority level",
                category=TemplateCategory.DECISION_MAKING,
                question="How should we prioritize these features?",
                options=["🔴 High Priority", "🟡 Medium Priority", "🟢 Low Priority", "⚪ Not Important"],
                vote_type="multiple",
                suggested_duration=120,
                tags=["priority", "ranking", "features"],
                created_at=datetime.now()
            ),
            
            # Team Feedback Templates
            PollTemplate(
                id="retrospective-feedback",
                name="Sprint Retrospective",
                description="Gather feedback on sprint performance",
                category=TemplateCategory.TEAM_FEEDBACK,
                question="How did our last sprint go?",
                options=["🚀 Excellent", "👍 Good", "😐 Average", "👎 Poor", "💥 Terrible"],
                vote_type="single",
                suggested_duration=30,
                tags=["retrospective", "sprint", "feedback"],
                created_at=datetime.now()
            ),
            
            PollTemplate(
                id="team-satisfaction",
                name="Team Satisfaction Survey",
                description="Measure team satisfaction and morale",
                category=TemplateCategory.TEAM_FEEDBACK,
                question="How satisfied are you with our current team dynamics?",
                options=["😄 Very Satisfied", "🙂 Satisfied", "😐 Neutral", "😕 Dissatisfied", "😞 Very Dissatisfied"],
                vote_type="single",
                suggested_duration=180,
                tags=["satisfaction", "morale", "team"],
                created_at=datetime.now()
            ),
            
            # Planning Templates
            PollTemplate(
                id="meeting-time",
                name="Meeting Time Selection",
                description="Find the best time for team meetings",
                category=TemplateCategory.PLANNING,
                question="When should we schedule our next team meeting?",
                options=["🌅 Morning (9-11 AM)", "🌞 Midday (11 AM-1 PM)", "🌤️ Afternoon (1-3 PM)", "🌆 Late Afternoon (3-5 PM)"],
                vote_type="multiple",
                suggested_duration=60,
                tags=["meeting", "schedule", "time"],
                created_at=datetime.now()
            ),
            
            PollTemplate(
                id="project-timeline",
                name="Project Timeline",
                description="Decide on project timeline and milestones",
                category=TemplateCategory.PLANNING,
                question="What timeline works best for this project?",
                options=["⚡ 1 Week", "🏃 2 Weeks", "🚶 1 Month", "🐌 2+ Months"],
                vote_type="single",
                suggested_duration=90,
                tags=["timeline", "project", "planning"],
                created_at=datetime.now()
            ),
            
            # Social Templates
            PollTemplate(
                id="lunch-choice",
                name="Lunch Selection",
                description="Choose where to go for team lunch",
                category=TemplateCategory.SOCIAL,
                question="Where should we go for lunch today?",
                options=["🍕 Pizza", "🍔 Burgers", "🍜 Asian Food", "🥗 Healthy Options", "🌮 Mexican Food"],
                vote_type="single",
                suggested_duration=15,
                tags=["lunch", "social", "food"],
                created_at=datetime.now()
            ),
            
            PollTemplate(
                id="team-activity",
                name="Team Building Activity",
                description="Choose team building activities",
                category=TemplateCategory.SOCIAL,
                question="What team building activity should we do?",
                options=["🎮 Gaming Session", "🍻 Happy Hour", "🎳 Bowling", "🎬 Movie Night", "🏃 Sports Activity"],
                vote_type="multiple",
                suggested_duration=120,
                tags=["team building", "activity", "social"],
                created_at=datetime.now()
            ),
            
            # Meeting Templates
            PollTemplate(
                id="meeting-agenda",
                name="Meeting Agenda Items",
                description="Prioritize agenda items for upcoming meeting",
                category=TemplateCategory.MEETING,
                question="Which topics should we prioritize in our next meeting?",
                options=["📊 Project Updates", "💡 New Ideas", "❓ Q&A Session", "📋 Action Items Review", "🔄 Process Improvements"],
                vote_type="multiple",
                suggested_duration=45,
                tags=["meeting", "agenda", "priorities"],
                created_at=datetime.now()
            ),
            
            # Product Templates
            PollTemplate(
                id="feature-feedback",
                name="Feature Feedback",
                description="Gather feedback on new product features",
                category=TemplateCategory.PRODUCT,
                question="How do you feel about our new feature?",
                options=["🎉 Love it!", "👍 Like it", "😐 It's okay", "👎 Don't like it", "❌ Hate it"],
                vote_type="single",
                suggested_duration=240,
                tags=["feature", "feedback", "product"],
                created_at=datetime.now()
            ),
            
            PollTemplate(
                id="ui-design-choice",
                name="UI Design Choice",
                description="Choose between design alternatives",
                category=TemplateCategory.PRODUCT,
                question="Which design approach do you prefer?",
                options=["🎨 Option A", "🖌️ Option B", "✏️ Option C", "🎭 Something else"],
                vote_type="single",
                suggested_duration=60,
                tags=["design", "ui", "choice"],
                created_at=datetime.now()
            )
        ]
        
        for template in default_templates:
            self.templates[template.id] = template
    
    def get_template(self, template_id: str) -> Optional[PollTemplate]:
        """Get a specific template by ID."""
        return self.templates.get(template_id)
    
    def get_templates_by_category(self, category: TemplateCategory) -> List[PollTemplate]:
        """Get all templates in a specific category."""
        return [t for t in self.templates.values() if t.category == category]
    
    def get_all_templates(self) -> List[PollTemplate]:
        """Get all available templates."""
        return list(self.templates.values())
    
    def search_templates(self, query: str) -> List[PollTemplate]:
        """Search templates by name, description, or tags."""
        query_lower = query.lower()
        matches = []
        
        for template in self.templates.values():
            if (query_lower in template.name.lower() or 
                query_lower in template.description.lower() or
                any(query_lower in tag.lower() for tag in template.tags)):
                matches.append(template)
        
        return matches
    
    def add_custom_template(self, template: PollTemplate) -> bool:
        """Add a custom template."""
        try:
            if template.id in self.templates:
                logger.warning(f"Template with ID {template.id} already exists")
                return False
            
            self.templates[template.id] = template
            logger.info(f"Added custom template: {template.name}")
            return True
        
        except Exception as e:
            logger.error(f"Error adding custom template: {e}")
            return False
    
    def update_template_usage(self, template_id: str):
        """Update template usage count."""
        if template_id in self.templates:
            self.templates[template_id].usage_count += 1
    
    def get_popular_templates(self, limit: int = 5) -> List[PollTemplate]:
        """Get most popular templates by usage count."""
        sorted_templates = sorted(
            self.templates.values(),
            key=lambda t: t.usage_count,
            reverse=True
        )
        return sorted_templates[:limit]
    
    def export_templates(self) -> str:
        """Export all templates to JSON."""
        templates_data = []
        for template in self.templates.values():
            template_dict = asdict(template)
            template_dict['category'] = template.category.value
            template_dict['created_at'] = template.created_at.isoformat()
            templates_data.append(template_dict)
        
        return json.dumps(templates_data, indent=2)
    
    def import_templates(self, json_data: str) -> bool:
        """Import templates from JSON."""
        try:
            templates_data = json.loads(json_data)
            
            for template_data in templates_data:
                template = PollTemplate(
                    id=template_data['id'],
                    name=template_data['name'],
                    description=template_data['description'],
                    category=TemplateCategory(template_data['category']),
                    question=template_data['question'],
                    options=template_data['options'],
                    vote_type=template_data['vote_type'],
                    suggested_duration=template_data['suggested_duration'],
                    tags=template_data['tags'],
                    created_at=datetime.fromisoformat(template_data['created_at']),
                    usage_count=template_data.get('usage_count', 0)
                )
                
                self.templates[template.id] = template
            
            logger.info(f"Imported {len(templates_data)} templates")
            return True
        
        except Exception as e:
            logger.error(f"Error importing templates: {e}")
            return False

# Global template manager instance
template_manager = TemplateManager()

# Utility functions
def get_template_by_id(template_id: str) -> Optional[PollTemplate]:
    """Get template by ID."""
    return template_manager.get_template(template_id)

def get_templates_by_category(category: str) -> List[PollTemplate]:
    """Get templates by category."""
    try:
        cat_enum = TemplateCategory(category)
        return template_manager.get_templates_by_category(cat_enum)
    except ValueError:
        return []

def search_templates(query: str) -> List[PollTemplate]:
    """Search templates."""
    return template_manager.search_templates(query)

def get_popular_templates(limit: int = 5) -> List[PollTemplate]:
    """Get popular templates."""
    return template_manager.get_popular_templates(limit)

def create_poll_from_template(template_id: str, custom_question: str = None) -> Optional[Dict[str, Any]]:
    """Create poll data from template."""
    template = template_manager.get_template(template_id)
    if not template:
        return None
    
    # Update usage count
    template_manager.update_template_usage(template_id)
    
    # Create poll data
    poll_data = {
        'question': custom_question or template.question,
        'options': template.options.copy(),
        'vote_type': template.vote_type,
        'suggested_duration': template.suggested_duration,
        'template_id': template_id,
        'template_name': template.name
    }
    
    return poll_data

def get_template_categories() -> List[Dict[str, str]]:
    """Get all template categories."""
    return [
        {'id': cat.value, 'name': cat.value.replace('_', ' ').title()}
        for cat in TemplateCategory
    ]