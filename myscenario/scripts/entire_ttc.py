# ライブラリのインポート
import numpy as np
import pandas as pd
import os
import math


def get_distance(x1, y1, x2, y2):
    d = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return d


def get_relative_speed(speed1, speed2):
    v = math.fabs(speed1 - speed2)
    return v


def get_ttc(d, v):
    return d / v


ttc_suggestion_3am_3 = list()
ttc_suggestion_3am_5 = list()
ttc_suggestion_3am_10 = list()
ttc_suggestion_8am_3 = list()
ttc_suggestion_8am_5 = list()
ttc_suggestion_8am_10 = list()

# 必要パラメータ
schedule = ['3am', '8am']
threshold = [3, 5, 10]

# ループ処理
for s in schedule:
    for t in threshold:
        # ttcリストの初期化
        ttc_list = list()

        # ファイルのパス指定
        veh_data = '../output/suggestion/{}/change_num_10/threshold_{}/veh_data.csv'.format(s, t)
        print(os.path.exists(veh_data))

        pseud_data = '../output/suggestion/{}/change_num_10/threshold_{}/pseud_change.csv'.format(s, t)
        print(os.path.exists(pseud_data))

        # csvファイルの読み込み
        veh_df = pd.read_csv(veh_data)
        pseud_df = pd.read_csv(pseud_data)

        virtual_veh_data = pseud_df[pseud_df['id'].str.contains('virtual')].id.values

        for virtual_veh_id in virtual_veh_data:
            # 仮想車両が生成されたタイミングのstepを取得
            step = int(virtual_veh_id.split('_')[2]) + 1
            # 仮想車両が走行している道路IDを出す
            v_veh_data = veh_df[(veh_df['id'] == virtual_veh_id) & (veh_df['step'] == step)]
            if len(v_veh_data) < 1:
                continue

            v_veh_route_id = v_veh_data.route_id.values[0]
            v_veh_pos_x = v_veh_data.pos_x.values[0]
            v_veh_pos_y = v_veh_data.pos_y.values[0]
            v_veh_speed = v_veh_data.speed.values[0]

            around_veh_data = veh_df[(veh_df['step'] == step) & (veh_df['route_id'] == v_veh_route_id) & (~veh_df['id'].str.contains('virtual'))]
            if len(around_veh_data) < 1:
                continue

            for _, around_veh_id in around_veh_data.iterrows():
                around_veh_route_id = around_veh_data.route_id.values[0]
                around_veh_pos_x = around_veh_data.pos_x.values[0]
                around_veh_pos_y = around_veh_data.pos_y.values[0]
                around_veh_speed = around_veh_data.speed.values[0]

                distance = get_distance(v_veh_pos_x, v_veh_pos_y, around_veh_pos_x, around_veh_pos_y)
                if distance > 300:
                    continue

                speed = get_relative_speed(v_veh_speed, around_veh_speed)
                if speed <= 1:
                    continue

                ttc = get_ttc(distance, speed)

                exec("ttc_suggestion_{}_{}".format(s, t) + ".append(ttc)")

# 平均エントロピー
excel_ttc_df = pd.DataFrame(
    data={
        ('suggestion', 'threshold=3(3am)'): pd.Series(data=ttc_suggestion_3am_3),
        ('suggestion', 'threshold=3(8am)'): pd.Series(data=ttc_suggestion_8am_3),
        ('suggestion', 'threshold=5(3am)'): pd.Series(data=ttc_suggestion_3am_5),
        ('suggestion', 'threshold=5(8am)'): pd.Series(data=ttc_suggestion_8am_5),
        ('suggestion', 'threshold=10(3am)'): pd.Series(data=ttc_suggestion_3am_10),
        ('suggestion', 'threshold=10(8am)'): pd.Series(data=ttc_suggestion_8am_10),
    },
)

# Excelファイルに出力
with pd.ExcelWriter('eval_ttc.xlsx') as writer:
    excel_ttc_df.to_excel(writer, sheet_name='travel time')

