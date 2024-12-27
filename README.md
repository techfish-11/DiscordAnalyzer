# EvexDevelopers SupportBot
Discordサーバーを分析するBot。EvexDevelopers向けに開発

# 使用方法
Tokenをmain.pyの一番下のコードに貼り付けてください
main.pyの22, 24, 26行目にあなたの環境に合うIDを設定してください

# 動作
1. 起動時に、サーバーの全メンバーのidと参加日を取得し、members.dbに保存します。※
2. on messageで、すべてのメッセージ数をカウントします。
3. コマンドに反応します。!helpcommandsでヘルプが見れます。
   
※初回だけではなく、毎回その動作を行います。
