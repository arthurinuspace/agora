# 🗳️ Agora - Slack向けエンタープライズ匿名投票システム

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![SOLID](https://img.shields.io/badge/Architecture-SOLID-yellow.svg)](./SOLID_ARCHITECTURE.md)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)

**Agora** は、チーム意思決定のための包括的な匿名投票ツールを提供する、本格的なエンタープライズ級Slackワークスペースアプリケーションです。SOLID アーキテクチャ原則で構築され、高度な分析、ロール管理、スケジューリング自動化、Web管理ダッシュボードを提供します。

## 📚 ドキュメント

本プロジェクトのドキュメントは完全にモジュール化されています。以下の専門ドキュメントを参照してください：

### 🎯 コアドキュメント
- **[概要](docs/overview.md)** - プロジェクト概要とコア機能
- **[クイックスタート](docs/quick-start.md)** - クイックスタートガイド
- **[インストール](docs/installation.md)** - 詳細なインストールガイド
- **[設定](docs/configuration.md)** - 設定説明
- **[使用ガイド](docs/usage.md)** - 使用ガイドと例

### 🏗️ アーキテクチャドキュメント
- **[SOLIDアーキテクチャ](SOLID_ARCHITECTURE.md)** - 完全アーキテクチャドキュメント
- **[技術スタック](docs/architecture/tech-stack.md)** - 技術スタック説明
- **[APIドキュメント](docs/api.md)** - RESTful API リファレンス

### 🔧 開発・デプロイ
- **[開発環境セットアップ](docs/development/setup.md)** - 開発環境セットアップ
- **[Dockerデプロイ](docs/deployment/docker.md)** - Dockerデプロイガイド
- **[本番環境デプロイ](DEPLOYMENT.md)** - 本番環境デプロイ

### 🛡️ セキュリティ・管理
- **[セキュリティガイド](docs/security.md)** - セキュリティベストプラクティス
- **[管理者ガイド](docs/admin.md)** - 管理者ガイド
- **[モニタリング](docs/monitoring.md)** - モニタリングとログ

### 🧪 テスト・品質
- **[テストガイド](TEST_SUMMARY.md)** - テストガイド
- **[テストガイドライン](docs/testing/guidelines.md)** - テスト要件
- **[パフォーマンステスト](docs/testing/performance.md)** - パフォーマンステスト

## ✨ 主要機能

詳細な機能説明は [概要](docs/overview.md) ドキュメントを参照してください。

### 🗳️ コア投票機能
- **🔒 完全匿名**: 投票者のアイデンティティと選択を完全に分離
- **📊 複数の投票タイプ**: 単一選択、複数選択、ランキング投票
- **⏰ リアルタイム更新**: 投票結果のリアルタイム更新
- **🛡️ 重複投票防止**: 設定可能な重複投票防止メカニズム

### 📈 高度な分析と洞察
- **📊 豊富なデータビジュアライゼーション**: インタラクティブなチャートとグラフ
- **📋 エクスポート機能**: CSV、JSON、Excel形式のエクスポート
- **🎯 参加分析**: 参加度と反応パターンの追跡
- **📈 トレンド分析**: 過去の投票パターンと洞察

### 🏗️ エンタープライズ級アーキテクチャ
- **🎯 SOLID準拠**: 8.8/10のアーキテクチャスコア（42%向上）
- **🔧 依存性注入**: 完全なサービスコンテナシステム
- **📦 モジュラー設計**: 13のサービスインターフェースと戦略パターン
- **🧪 包括的テスト**: ユニット、統合、パフォーマンステスト

## 🚀 クイックスタート

完全なクイックスタートガイドは [クイックスタートガイド](docs/quick-start.md) を参照してください。

### 基本要件
- **Python 3.12+**
- **Docker & Docker Compose**（本番環境）
- **Slack App** ボット権限
- **ngrok**（ローカル開発）

### 簡単インストール
```bash
# リポジトリをクローン
git clone https://github.com/arthurinuspace/agora.git
cd agora

# 仮想環境をセットアップ
python3 -m venv venv
source venv/bin/activate

# 依存関係をインストール
pip install -r requirements.txt

# 環境変数を設定
cp .env.example .env
# .env を編集してSlack認証情報を入力

# データベースを初期化
python database.py

# アプリケーションを起動
python start_slack_app.py
```

詳細なインストールガイドは以下を参照してください：
- [インストールガイド](docs/installation.md) - 詳細なインストール説明
- [設定ガイド](docs/configuration.md) - 設定

## 📱 Slack設定

完全な設定ガイドは [設定ガイド](docs/configuration.md) を参照してください。

### 必要なボット権限
```
commands          # スラッシュコマンド
chat:write        # メッセージ送信
chat:write.public # パブリックチャンネル送信
users:read        # ユーザー情報読み取り
channels:read     # チャンネル情報読み取り
```

### スラッシュコマンド設定
- **コマンド**: `/agora`
- **リクエストURL**: `https://your-domain.com/slack/events`
- **説明**: 匿名投票の作成と管理

## 💡 使用例

詳細な使用ガイドは [使用ガイド](docs/usage.md) を参照してください。

### 基本投票の作成
```
/agora 昼食は何を食べますか？
```

### 複数選択投票の作成
```
/agora 優先すべき機能はどれですか？（複数選択）
```

### モーダルインターフェースの使用
1. 任意の質問とともに `/agora` を使用
2. モーダルウィンドウが開き、以下が可能：
   - 投票質問の編集
   - 複数選択肢の追加（1行に1つ）
   - 投票タイプの選択（単一選択/複数選択）
   - スケジューリングオプションの設定
   - 匿名設定の構成

## 🏗️ アーキテクチャ概要

完全なアーキテクチャ説明は [SOLIDアーキテクチャ](SOLID_ARCHITECTURE.md) ドキュメントを参照してください。

### 技術スタック
- **バックエンド**: FastAPI (Python 3.12+)
- **データベース**: SQLite (開発) / PostgreSQL (本番)
- **キャッシュ**: Redis（セッションとパフォーマンス用）
- **フロントエンド**: HTML/CSS/JavaScript レスポンシブデザイン
- **デプロイ**: Docker コンテナ + Nginx リバースプロキシ
- **テスト**: pytest 包括的テストスイート

### SOLIDアーキテクチャ設計
```
agora/
├── services/              # 依存性注入サービス層
│   ├── abstractions.py   # 13のサービスインターフェース
│   ├── implementations.py # 具体的実装
│   ├── container.py      # DIコンテナ
│   └── factory.py        # サービスファクトリ
├── strategies/            # 戦略パターン
│   ├── validation.py     # 5つの検証戦略
│   └── export.py         # 3つのエクスポート戦略
├── api/                  # モジュラーAPIエンドポイント
│   ├── auth.py          # 認証
│   ├── polls.py         # 投票操作
│   └── admin.py         # 管理コンソール
└── database/             # データベース層
```

詳細なアーキテクチャ説明は以下を参照してください：
- [技術スタック](docs/architecture/tech-stack.md) - 技術スタック詳細
- [SOLID原則](docs/architecture/solid-principles.md) - SOLID原則の実装

## 🧪 開発

完全な開発ガイドは [開発環境セットアップ](docs/development/setup.md) を参照してください。

### テストの実行
```bash
# 仮想環境をアクティベート
source venv/bin/activate

# すべてのテストを実行
python -m pytest -v

# SOLIDアーキテクチャテストを実行
python -m pytest test_solid_architecture.py -v

# 完全なテストスイートを実行
python -m pytest test_enhanced_*.py test_integration_*.py -v
```

### 開発コマンド
```bash
# 開発サーバーを起動
python -m uvicorn main:app --reload --port 8000

# データベースマイグレーションを実行
python database.py

# ヘルスチェック
curl http://localhost:8000/health
```

詳細な開発ガイドは以下を参照してください：
- [開発ワークフロー](docs/development/workflow.md) - 開発フロー
- [コード標準](docs/development/standards.md) - コード標準
- [テストガイドライン](docs/testing/guidelines.md) - テストガイド

## 🐳 Dockerデプロイ

完全なデプロイガイドは [Dockerデプロイ](docs/deployment/docker.md) を参照してください。

### 開発環境
```bash
# すべてのサービスを起動
docker-compose up -d

# ログを確認
docker-compose logs -f agora
```

### 本番環境
```bash
# SSL付き本番デプロイ
docker-compose -f docker-compose.prod.yml up -d

# サービスをスケール
docker-compose -f docker-compose.prod.yml up -d --scale agora=3
```

### Dockerサービス
- **agora**: メインアプリケーションサーバー
- **postgres**: PostgreSQLデータベース（本番）
- **redis**: Redisキャッシュとセッション
- **nginx**: SSL付きリバースプロキシ（本番）

詳細なデプロイガイドは以下を参照してください：
- [本番環境デプロイ](DEPLOYMENT.md) - 本番環境デプロイ
- [Dockerデプロイ](docs/deployment/docker.md) - Dockerデプロイ詳細

## 📊 モニタリングと分析

完全なモニタリングガイドは [モニタリングガイド](docs/monitoring.md) を参照してください。

### 内蔵モニタリング機能
- **ヘルスチェック**: `/health` エンドポイントがサービス状態を提供
- **メトリクス**: `/metrics` エンドポイントがPrometheus互換メトリクスを提供
- **パフォーマンス**: リクエスト時間とリソース使用量
- **エラー追跡**: 包括的なエラーログとアラート

### Webコンソール
`https://your-domain.com/admin` の管理コンソールにアクセス：
- リアルタイム投票モニタリング
- ユーザー参加度分析
- システムヘルスとパフォーマンスメトリクス
- エクスポートとレポートツール

## 🤝 貢献

貢献を歓迎します！詳細は [貢献ガイドライン](./CONTRIBUTING.md) を参照してください。

### 開発セットアップ
1. リポジトリをフォーク
2. 機能ブランチを作成: `git checkout -b feature/amazing-feature`
3. SOLID原則に従って変更を行う
4. 包括的なテストを追加
5. すべてのテストが通ることを確認: `python -m pytest`
6. プルリクエストを提出

### コード標準
- PEP 8 スタイルガイドに従う
- SOLIDアーキテクチャ原則を維持
- 包括的なテストを書く（>80%カバレッジ）
- すべてのパブリックAPIを文書化
- 型ヒントを使用

## 🔒 セキュリティ

完全なセキュリティガイドは [セキュリティガイド](docs/security.md) を参照してください。

- **リクエスト検証**: すべてのSlackリクエストが検証される
- **環境変数**: すべての機密データは環境変数を使用
- **SQLインジェクション保護**: SQLAlchemy ORMとパラメータ化クエリ
- **レート制限**: APIエンドポイントに内蔵レート制限
- **監査ログ**: 完全なアクション監査トレイル

## 📄 ドキュメント

### 主要ドキュメント
- **[SOLIDアーキテクチャ](./SOLID_ARCHITECTURE.md)**: 詳細なアーキテクチャドキュメント
- **[デプロイガイド](./DEPLOYMENT.md)**: 完全なデプロイガイド
- **[テストガイド](./TEST_SUMMARY.md)**: 包括的なテストドキュメント
- **[貢献ガイド](./CONTRIBUTING.md)**: 貢献者ガイド

### 完全なドキュメントシステム
本READMEトップの [📚 ドキュメント](#-ドキュメント) セクションを参照してください。すべてのモジュラードキュメントへのリンクが含まれています。

## 📝 ライセンス

本プロジェクトはMITライセンスの下でライセンスされています - 詳細は [LICENSE](./LICENSE) ファイルを参照してください。

## 🎯 サポートとコミュニティ

- **Issues**: [GitHub Issues](https://github.com/arthurinuspace/agora/issues)
- **ディスカッション**: [GitHub Discussions](https://github.com/arthurinuspace/agora/discussions)
- **ドキュメント**: [Wiki](https://github.com/arthurinuspace/agora/wiki)

## 🏆 謝辞

- [FastAPI](https://fastapi.tiangolo.com/) と [Slack Bolt](https://slack.dev/bolt-python/) で構築
- 民主的意思決定原則にインスパイア
- 保守性と拡張性を確保するためSOLID原則に従ったアーキテクチャ

---

**Made with ❤️ for better team collaboration**

*Agora - すべての声が重要、匿名で。*