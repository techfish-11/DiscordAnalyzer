# EvexDevelopers SupportBot

EvexDevelopers SupportBotは、EvexDevelopers向けに開発されたDiscordボットです。このボットは、サーバーのメンバー数の管理やメッセージ数の記録、成長率の計算などを行います。

## 機能

- メンバー数の記録と表示
- メッセージ数の記録と表示
- サーバーの成長率の計算
- 1000人達成時の通知

## インストール

1. このリポジトリをクローンします。

    ```sh
    git clone https://github.com/techfish-11/EvexDevelopers-SupportBot.git
    cd EvexDevelopers-SupportBot
    ```

2. 必要なパッケージをインストールします。

    ```sh
    pip install -r requirements.txt
    ```

3. 

main.py

 ファイルの 

bot.run('your_token_here')

 をあなたのDiscordボットのトークンに置き換えます。

## 使用方法

1. ボットを起動します。

    ```sh
    python main.py
    ```

2. 以下のコマンドを使用して、ボットの機能を利用できます。

    - `!1000`: 現在のメンバー数と1000人達成までの残り人数を表示します。
    - `!progress`: 1000人達成までの進捗率を表示します。
    - `!helpcommands`: サポートボットのコマンド一覧を表示します。
    - `!growth`: サーバーの成長率を計算し、グラフを表示します。
    - `!messagegraph`: 日別メッセージ数のグラフを表示します。

## データベース

このボットはSQLiteデータベースを使用して、メンバー数やメッセージ数を記録します。データベースファイルは 

members.db

 です。

## 貢献

バグ報告や機能リクエストは、Issueを作成してください。プルリクエストも歓迎します。

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は `LICENSE` ファイルを参照してください。

## 開発者

EvexDevelopers SupportBotは、EvexDevelopers向けに開発されました。
