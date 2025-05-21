# Test Manager Application

Djangoベースのテスト管理用アプリケーションです。

ここで言う「テスト」とは、主に手動でWebブラウザ等を操作することでテスト対象となるWebアプリケーションが期待通りに動作するかを確認する作業を指します。
継続的に品質管理をする上で、このTest Managerアプリのシナリオをソフトウェアリリース前に随時実装することを想定しています。


## 画面イメージ

![画面イメージ1](misc/screen1.png)

![画面イメージ2](misc/screen2.png)

![画面イメージ3](misc/screen3.png)


## 大まかな使い方

0. ログイン画面からユーザー認証を行います
1. 対象のソフトウェアごとに「プロジェクト」を準備します
2. プロジェクトの中で「テストケース」を作成します。
    * 一つの「テストケース」は複数の「テストステップ」を記述でき、それぞれに「手順」と「期待する結果」を分けて記述できます。
3. 実際に一連のテスト作業を実行する段階で、「テストセッション」を作成します
    * その一回のテスト作業で使用する「テストケース」を選びセッションに含めます
4. テストセッションに含まれているテストをテスターに実行してもらいます。
    * 実行結果によってセッションごとのテスト成功数・失敗数などを記録しておけます
5. テストセッションを通じたテスト作業を繰り返し実行することで、プロジェクト内でのソフトウェア品質の変遷を管理します

[misc/sample_data.csv](misc/sample_data.csv) にインポート可能なプロジェクト用CSVファイルがあります。


## 開発者向け情報

### プロジェクト構成

このプロジェクトは以下のコンポーネントで構成されています：

- **test_manager**: Djangoプロジェクトのメインディレクトリ
- **test_tracking**: テスト管理機能を提供するDjangoアプリケーション

### 使用技術

- Python 3.13 + [uv](https://github.com/astral-sh/uv)
- Django 5.2
- pytest + pytest-django + pytest-cov

Python 3.13をビルド出来るようにしておく必要があります。
例えば Ubuntu 24.04 LTSの場合は以下のように先に関連パッケージをインストールしてください

```bash
sudo apt -y install \
    libxml2-dev libssl-dev libbz2-dev libcurl4-openssl-dev libjpeg-dev libpng-dev libmcrypt-dev \
    libreadline-dev libtidy-dev libxslt-dev autoconf \
    sqlite3 libsqlite3-dev libonig-dev libzip-dev pkg-config php-cli php-mbstring unzip
```

### 基本的な使い方

#### 開発用サーバの起動

```bash
uv run manage.py runserver
```

#### テストの実行

```bash
uv run pytest
```

## API

#### OpenAPI 関連

APIドキュメントの自動生成を目的に[drf-speculator](https://github.com/tfranzel/drf-spectacular/)を導入しています。

* api/schema/ ... schema.yml をダウンロード
* api/schema/swagger-ui/ ... Swagger UI
* api/schema/redoc/ ... redoc UI

```bash
uv run manage.py spectacular --color --file schema.yml
docker run -p 8080:8080 -e SWAGGER_JSON=/schema.yml -v ${PWD}/schema.yml:/schema.yml swaggerapi/swagger-ui
```


## ライセンス

このプロジェクトはMITライセンスの下で公開されています - 詳細は[LICENSE](LICENSE)ファイルを参照してください。

### REST API
- Project一覧APIを追加
    - Django Rest Frameworkによる実装を `views.py` から `api.py` に分離しました。
    - `urls.py` を更新し、`api.py` の `ProjectList` ビューを使用するようにしました。
- API認証機能の追加
    - Django REST Framework の `TokenAuthentication` を導入し、API呼び出しに認証トークンを必須としました。
    - ユーザーは `/api/api-token-auth/` エンドポイントで認証情報を送信することでAPIトークンを取得できます。
- ユーザー管理機能の追加
    - 管理者向けにユーザー一覧、ユーザー情報（姓名）編集、APIトークン発行・再発行機能を持つ画面を追加しました。
    - `/users/` からアクセス可能です。
