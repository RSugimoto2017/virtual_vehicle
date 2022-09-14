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

delta_x = [_ for _ in range(-5, 6)]
delta_y = [_ for _ in range(-5, 6)]
candidate_points = []
for x in delta_x:
    for y in delta_y:
        candidate_points.append(x * y)

# 平均エントロピー初期化
entropy_normal_3am_3 = np.zeros(11)
entropy_normal_3am_5 = np.zeros(11)
entropy_normal_3am_10 = np.zeros(11)
entropy_normal_8am_3 = np.zeros(11)
entropy_normal_8am_5 = np.zeros(11)
entropy_normal_8am_10 = np.zeros(11)
entropy_suggestion_3am_3 = np.zeros(11)
entropy_suggestion_3am_5 = np.zeros(11)
entropy_suggestion_3am_10 = np.zeros(11)
entropy_suggestion_8am_3 = np.zeros(11)
entropy_suggestion_8am_5 = np.zeros(11)
entropy_suggestion_8am_10 = np.zeros(11)

# 生成できたMix Zoneの数（必要だったらやる）
mix_zone_normal_3am_3 = np.zeros(11)
mix_zone_normal_3am_5 = np.zeros(11)
mix_zone_normal_3am_10 = np.zeros(11)
mix_zone_normal_8am_3 = np.zeros(11)
mix_zone_normal_8am_5 = np.zeros(11)
mix_zone_normal_8am_10 = np.zeros(11)
mix_zone_suggestion_3am_3 = np.zeros(11)
mix_zone_suggestion_3am_5 = np.zeros(11)
mix_zone_suggestion_3am_10 = np.zeros(11)
mix_zone_suggestion_8am_3 = np.zeros(11)
mix_zone_suggestion_8am_5 = np.zeros(11)
mix_zone_suggestion_8am_10 = np.zeros(11)

# ループ処理
for m in method:
    for s in schedule:
        for t in threshold:
            # ファイルのパス指定
            pseudo_data = '../output/{}/{}/change_num_10/threshold_{}/pseud_change.csv'.format(m, s, t)

            # csvファイルの読み込み
            pseud_df = pd.read_csv(pseudo_data)

            for n in range(1, change_pseudo_num + 1):
                pseud_change_step = period * n
                print(pseud_change_step)
                mix_zone_num = 0
                entropy = 0

                for index, point in enumerate(candidate_points):
                    quantity = pseud_df[(pseud_df['step'] == pseud_change_step) & (pseud_df['candidate_point'] == index)]
                    if not quantity.empty and len(quantity.id.values) >= t:
                        mix_zone_num += 1
                        entropy += np.log2(len(quantity.id.values))

                if mix_zone_num > 0:
                    mean_entropy = entropy / mix_zone_num
                else:
                    mean_entropy = 0

                print(mix_zone_num / len(candidate_points), mean_entropy)
                exec("entropy_{}_{}_{}".format(m, s, t) + "[n] = mean_entropy")
                exec("mix_zone_{}_{}_{}".format(m, s, t) + "[n] = mix_zone_num / len(candidate_points)")

# 平均エントロピー
excel_entropy_df = pd.DataFrame(
    data={
        ('normal', 'threshold=3(3am)'): pd.Series(data=entropy_normal_3am_3),
        ('normal', 'threshold=3(8am)'): pd.Series(data=entropy_normal_8am_3),
        ('normal', 'threshold=5(3am)'): pd.Series(data=entropy_normal_3am_5),
        ('normal', 'threshold=5(8am)'): pd.Series(data=entropy_normal_8am_5),
        ('normal', 'threshold=10(3am)'): pd.Series(data=entropy_normal_3am_10),
        ('normal', 'threshold=10(8am)'): pd.Series(data=entropy_normal_8am_10),
        ('suggestion', 'threshold=3(3am)'): pd.Series(data=entropy_suggestion_3am_3),
        ('suggestion', 'threshold=3(8am)'): pd.Series(data=entropy_suggestion_8am_3),
        ('suggestion', 'threshold=5(3am)'): pd.Series(data=entropy_suggestion_3am_5),
        ('suggestion', 'threshold=5(8am)'): pd.Series(data=entropy_suggestion_8am_5),
        ('suggestion', 'threshold=10(3am)'): pd.Series(data=entropy_suggestion_3am_10),
        ('suggestion', 'threshold=10(8am)'): pd.Series(data=entropy_suggestion_8am_10),
    },
    index=[_ for _ in range(10 + 1)]
)

# 生成できたMix Zoneの数
excel_mix_zone_df = pd.DataFrame(
    data={
        ('normal', 'threshold=3(3am)'): pd.Series(data=mix_zone_normal_3am_3),
        ('normal', 'threshold=3(8am)'): pd.Series(data=mix_zone_normal_8am_3),
        ('normal', 'threshold=5(3am)'): pd.Series(data=mix_zone_normal_3am_5),
        ('normal', 'threshold=5(8am)'): pd.Series(data=mix_zone_normal_8am_5),
        ('normal', 'threshold=10(3am)'): pd.Series(data=mix_zone_normal_3am_10),
        ('normal', 'threshold=10(8am)'): pd.Series(data=mix_zone_normal_8am_10),
        ('suggestion', 'threshold=3(3am)'): pd.Series(data=mix_zone_suggestion_3am_3),
        ('suggestion', 'threshold=3(8am)'): pd.Series(data=mix_zone_suggestion_8am_3),
        ('suggestion', 'threshold=5(3am)'): pd.Series(data=mix_zone_suggestion_3am_5),
        ('suggestion', 'threshold=5(8am)'): pd.Series(data=mix_zone_suggestion_8am_5),
        ('suggestion', 'threshold=10(3am)'): pd.Series(data=mix_zone_suggestion_3am_10),
        ('suggestion', 'threshold=10(8am)'): pd.Series(data=mix_zone_suggestion_8am_10),
    },
    index=[_ for _ in range(10 + 1)]
)

# Excelファイルに出力
with pd.ExcelWriter('eval_entropy.xlsx') as writer:
    excel_entropy_df.to_excel(writer, sheet_name='entropy')
    excel_mix_zone_df.to_excel(writer, sheet_name='mix zone')