# GMOコインでXEMの自動売買をするプログラム

## ファイル

-   main.py：プログラムを動かすためのファイル
-   gmocoin.py：GMOcoinクラスが書かれているファイル
-   config.ini：API Keyが書かれているファイル
-   requirements.txt：ライブラリ一覧が書かれているファイル
-   utils/notify.py：LINE通知用の関数が書かれているファイル

## 設定

1.   GMOコインの[アカウントを作る](https://coin.z.com/jp/corp/guide/flow/)
1.   GMOコインの[連携APIキーを取得し](https://cryptolinc.com/faq_cases/gmocoin_api_setting)、アクセスキー・シークレットキーをconfig.iniに書く
     ただし、**資産**、**トレード**の全ての欄にチェックを付ける
1.   LINE Notifyの[トークンを発行](https://www.smilevision.co.jp/blog/tsukatte01/)し、utils/notify.pyに書く
1.   XEM以外の暗号資産（Bitcoinなど）で売買したい場合、main.pyとgmocoin.pyのコード内の*XEM*を該当する銘柄に書き換える
     参照：https://api.coin.z.com/docs/?python#outline

## 起動

実際に起動させるためには、サーバをレンタルするかRaspberry Pi上で動かす

*Auto-Trade-main*フォルダ内でターミナルを開き、`python main.py`と入力して実行開始

実行開始後1週間はデータを取る期間のため、売買は行われない

停止させたい場合は、ターミナル上で***Ctrl***+***C***
