# ライブラリのインポート
import numpy as np
import pandas as pd
import os

travel_time_normal_3am_3 = 0
travel_time_normal_3am_5 = 0
travel_time_normal_3am_10 = 0
travel_time_normal_8am_3 = 0
travel_time_normal_8am_5 = 0
travel_time_normal_8am_10 = 0
travel_time_suggestion_3am_3 = 0
travel_time_suggestion_3am_5 = 0
travel_time_suggestion_3am_10 = 0
travel_time_suggestion_8am_3 = 0
travel_time_suggestion_8am_5 = 0
travel_time_suggestion_8am_10 = 0

# 必要パラメータ
method = ['normal', 'suggestion']
schedule = ['3am', '8am']
threshold = [3, 5, 10]

# ループ処理
for m in method:
    for s in schedule:
        for t in threshold:
            # ファイルのパス指定
            veh_data = '../output/{}/{}/change_num_10/threshold_{}/veh_data.csv'.format(m, s, t)
            print(os.path.exists(veh_data))

            # csvファイルの読み込み
            veh_df = pd.read_csv(veh_data)
            all_veh = [veh_id for veh_id in set(veh_df.id.values) if 'virtual' not in veh_id.split('_')]

            travel_time_list = list()
            for vehicle in all_veh:
                first_step = veh_df[veh_df['id'] == vehicle].iloc[0].step
                last_step = veh_df[veh_df['id'] == vehicle].iloc[-1].step
                travel_time_list.append(last_step - first_step)
            mean_travel_time = np.mean(travel_time_list)
            exec("travel_time_{}_{}_{}".format(m, s, t) + "= mean_travel_time")

excel_travel_time_df = pd.DataFrame(
    data={
        ('normal', 'threshold=3(3am)'): pd.Series(data=travel_time_normal_3am_3),
        ('normal', 'threshold=3(8am)'): pd.Series(data=travel_time_normal_8am_3),
        ('normal', 'threshold=5(3am)'): pd.Series(data=travel_time_normal_3am_5),
        ('normal', 'threshold=5(8am)'): pd.Series(data=travel_time_normal_8am_5),
        ('normal', 'threshold=10(3am)'): pd.Series(data=travel_time_normal_3am_10),
        ('normal', 'threshold=10(8am)'): pd.Series(data=travel_time_normal_8am_10),
        ('suggestion', 'threshold=3(3am)'): pd.Series(data=travel_time_suggestion_3am_3),
        ('suggestion', 'threshold=3(8am)'): pd.Series(data=travel_time_suggestion_8am_3),
        ('suggestion', 'threshold=5(3am)'): pd.Series(data=travel_time_suggestion_3am_5),
        ('suggestion', 'threshold=5(8am)'): pd.Series(data=travel_time_suggestion_8am_5),
        ('suggestion', 'threshold=10(3am)'): pd.Series(data=travel_time_suggestion_3am_10),
        ('suggestion', 'threshold=10(8am)'): pd.Series(data=travel_time_suggestion_8am_10),
    },
    index=[_ for _ in range(10 + 1)]
)

# Excelファイルに出力
with pd.ExcelWriter('eval_travel_time.xlsx') as writer:
    excel_travel_time_df.to_excel(writer, sheet_name='travel time')
