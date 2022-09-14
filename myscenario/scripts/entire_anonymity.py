# ライブラリのインポート
import numpy as np
import pandas as pd
import os

# 必要パラメータ
method = ['normal', 'suggestion']
schedule = ['3am', '8am']
change_pseudo_num = 10
threshold = [3, 5, 10]
total_step = 600
period = total_step // change_pseudo_num

# 平均匿名セット初期化
anonymity_normal_3am_3 = np.ones(11)
anonymity_normal_3am_5 = np.ones(11)
anonymity_normal_3am_10 = np.ones(11)
anonymity_normal_8am_3 = np.ones(11)
anonymity_normal_8am_5 = np.ones(11)
anonymity_normal_8am_10 = np.ones(11)
anonymity_suggestion_3am_3 = np.ones(11)
anonymity_suggestion_3am_5 = np.ones(11)
anonymity_suggestion_3am_10 = np.ones(11)
anonymity_suggestion_8am_3 = np.ones(11)
anonymity_suggestion_8am_5 = np.ones(11)
anonymity_suggestion_8am_10 = np.ones(11)

# ループ処理
for m in method:
    for s in schedule:
        for t in threshold:
            # ファイルのパス指定
            veh_data = '../output/{}/{}/change_num_10/threshold_{}/veh_data.csv'.format(m, s, t)
            pseudo_data = '../output/{}/{}/change_num_10/threshold_{}/pseud_change.csv'.format(m, s, t)
            print(os.path.exists(veh_data))
            print(os.path.exists(pseudo_data))

            # csvファイルの読み込み
            veh_df = pd.read_csv(veh_data)
            pseud_df = pd.read_csv(pseudo_data)

            for n in range(1, change_pseudo_num + 1):
                pseud_change_step = period * n

                all_veh = [veh_id for veh_id in set(veh_df[veh_df['step'] == pseud_change_step].id.values)
                           if 'virtual' not in veh_id.split('_')]
                all_veh_count = len(all_veh)

                # 匿名セット，エントロピーの計算
                eval_anonymity = {veh_id: 1 for veh_id in all_veh}

                for veh_id in all_veh:
                    pseud_veh_id_df = pseud_df[pseud_df['id'] == veh_id]
                    if not pseud_veh_id_df.empty:
                        for column, item in pseud_veh_id_df.iterrows():
                            around_veh_df = pseud_df[(pseud_df['candidate_point'] == item.candidate_point)
                                                     & (pseud_df['step'] == pseud_change_step)]
                            if len(around_veh_df.id.values) >= t:
                                eval_anonymity[veh_id] += len(around_veh_df.id.values) - 1
                mean_anonymity = np.mean(list(eval_anonymity.values()))
                print(mean_anonymity)
                exec("anonymity_{}_{}_{}".format(m, s, t) + "[n] = mean_anonymity")
    # anonymity_3_3.append(mean_anonymity)

# Excelファイル出力用のデータフレームを作成
# 平均匿名セット
excel_anonymity_df = pd.DataFrame(
    data={
        ('normal', 'threshold=3(3am)'): pd.Series(data=anonymity_normal_3am_3),
        ('normal', 'threshold=3(8am)'): pd.Series(data=anonymity_normal_8am_3),
        ('normal', 'threshold=5(3am)'): pd.Series(data=anonymity_normal_3am_5),
        ('normal', 'threshold=5(8am)'): pd.Series(data=anonymity_normal_8am_5),
        ('normal', 'threshold=10(3am)'): pd.Series(data=anonymity_normal_3am_10),
        ('normal', 'threshold=10(8am)'): pd.Series(data=anonymity_normal_8am_10),
        ('suggestion', 'threshold=3(3am)'): pd.Series(data=anonymity_suggestion_3am_3),
        ('suggestion', 'threshold=3(8am)'): pd.Series(data=anonymity_suggestion_8am_3),
        ('suggestion', 'threshold=5(3am)'): pd.Series(data=anonymity_suggestion_3am_5),
        ('suggestion', 'threshold=5(8am)'): pd.Series(data=anonymity_suggestion_8am_5),
        ('suggestion', 'threshold=10(3am)'): pd.Series(data=anonymity_suggestion_3am_10),
        ('suggestion', 'threshold=10(8am)'): pd.Series(data=anonymity_suggestion_8am_10),
    },
    index=[_ for _ in range(10 + 1)]
)

# Excelファイルに出力
with pd.ExcelWriter('eval_anonymity.xlsx') as writer:
    excel_anonymity_df.to_excel(writer, sheet_name='anonymity')
