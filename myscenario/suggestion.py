#!/usr/bin/env python

import os
import sys
import optparse
import csv
import math
from sumolib import checkBinary
import traci

# 必要パラメータを記入
# on-peak(8am) か off-peak(3am)
schedule = sys.argv[1] + 'am'

# 仮名変更回数
change_pseudo_num = int(sys.argv[2])

# 仮名変更の閾値
threshold = int(sys.argv[3])

# ターゲットのファイル名
target = 'output/suggestion/{}/change_num_{}/threshold_{}/dua.actuated.sumocfg'.format(schedule, change_pseudo_num, threshold)

# 総ステップ数
total_step = 600

# 亜名を変更するまでの時間
time_to_change_pseudo = 5

# 通信範囲
communication_range = 300

# 出力用車両データ
veh_columns = ['step', 'id', 'pos_x', 'pos_y', 'speed', 'route_id', 'total_waiting_time']
veh_data = list()
veh_data.append(tuple(veh_columns))

# 仮名変更データ
pseud_columns = ['step', 'id', 'candidate_point', 'times']
pseud_data = list()
pseud_data.append(tuple(pseud_columns))


# $SUMO_HOME/toolsを指定する
def has_sumo_env():
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("please declare environment variable 'SUMO_HOME'")


# guiのオプションをロード
def get_options():
    opt_parser = optparse.OptionParser()
    opt_parser.add_option("--nogui", action="store_true", default=False, help="run the commandline version of sumo")
    options, args = opt_parser.parse_args()
    return options


# 候補地点の定義用関数
# 交差点のジャンクションの中で最も大きい10個を候補地点とする
def get_candidate_points():
    # 仮名交換候補地点の定義
    center = (6810.565, 5728.15)
    delta_x = [_ for _ in range(-5, 6)]
    delta_y = [_ for _ in range(-5, 6)]
    candidate_points = []
    width = 600
    for x in delta_x:
        for y in delta_y:
            tmp_x = center[0] + x * width
            tmp_y = center[1] + y * width
            candidate_points.append((tmp_x, tmp_y))

    return list(set(candidate_points))


# 候補地点からの距離を測定
def get_distance(x1, y1, x2, y2):
    d = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return d


# シミュレーションのフィードバックループ
def run():
    # シミュレーションステップの初期化
    step = 0
    times = 0
    begin_mode = False
    wait_mode = False
    virtual_vehicle_mode = False
    end_mode = False

    candidate_points = get_candidate_points()
    # 各円領域内にいる車両のIDリスト
    member_veh_ids_by_points = [[] for _ in range(len(candidate_points))]
    all_member_veh_ids = []
    # 円領域ごとの仮想車両の台数
    emitted_veh_num_by_points = [0 for _ in range(len(candidate_points))]
    # 仮想車両を出している車両の紐付け
    virtual_veh_dict = {}

    # シミュレーション時間が600sもしくは車両数が0以上になる
    while step <= total_step or traci.simulation.getMinExpectedNumber() > 0:
        begin_pseudo_change_time = (total_step // change_pseudo_num) * (times + 1) - time_to_change_pseudo
        end_pseudo_change_time = (total_step // change_pseudo_num) * (times + 1)
        # 仮名変更開始モード
        if step == begin_pseudo_change_time:
            begin_mode = True
            member_veh_ids_by_points = [[] for _ in range(len(candidate_points))]
            all_member_veh_ids = []
            emitted_veh_num_by_points = [0 for _ in range(len(candidate_points))]

        # 仮名変更待機モード
        if begin_pseudo_change_time < step < end_pseudo_change_time:
            wait_mode = True
            begin_mode = False

        # 仮想車両台数決定モード
        if step == end_pseudo_change_time - 1:
            virtual_vehicle_mode = True
            wait_mode = False

        # 仮名変更終了モード
        if step == end_pseudo_change_time:
            end_mode = True
            virtual_vehicle_mode = False

        # 仮名変更時刻が過ぎたら，どのモードにも入らないようにする
        # timesを更新
        if end_pseudo_change_time < step <= total_step + 1:
            end_mode = False
            if step <= total_step and times < change_pseudo_num - 1:
                times += 1

        # 追加した仮想車両が生きているかの判定
        delete_keys = list()
        for key, value in virtual_veh_dict.items():
            for virtual_veh_id in value:
                # 仮想車両が死んでいる場合は削除
                if virtual_veh_id in list(traci.vehicle.getIDList()):
                    continue

                value.remove(virtual_veh_id)
                virtual_veh_dict[key] = value
                print('deleted:', virtual_veh_id)
                if len(value) == 0:
                    delete_keys.append(key)

        # 仮想車両生成車両が生きているかの判断
        # すでに目的地に到着している場合は，virtual_veh_dictからそのキーを削除
        for key in virtual_veh_dict.keys():
            if key in list(traci.vehicle.getIDList()):
                continue
            delete_keys.append(key)
            print('arrived:', key)

        # 不要なキーを削除
        # 重複している場合を考慮してsetを使用
        for key in set(delete_keys):
            del virtual_veh_dict[key]

        # stepごとの車両のデータを取得
        for veh_id in traci.vehicle.getIDList():
            pos = traci.vehicle.getPosition(veh_id)
            speed = traci.vehicle.getSpeed(veh_id)
            routes = traci.vehicle.getRoute(veh_id)
            route_index = traci.vehicle.getRouteIndex(veh_id)
            rest_routes = list(routes[route_index:])
            route_id = traci.vehicle.getRouteID(veh_id)
            total_waiting_time = traci.vehicle.getAccumulatedWaitingTime(veh_id)
            veh_info = (step, veh_id, pos[0], pos[1], speed, routes[route_index], total_waiting_time)

            # 仮名変更直前から仮名更時刻まで
            # end_modeは解析時に閾値以上ないと仮名変更できないとする
            if begin_mode or wait_mode or virtual_vehicle_mode or end_mode:
                for index, point in enumerate(candidate_points):
                    dist = get_distance(pos[0], pos[1], point[0], point[1])
                    # 円領域から300m以上であるものは無視
                    if dist > communication_range:
                        # メンバー車両が300m外になった場合は，削除
                        if veh_id in member_veh_ids_by_points[index]:
                            member_veh_ids_by_points[index].remove(veh_id)
                            all_member_veh_ids.remove(veh_id)
                        continue

                    # メンバー車両が300m以内にいる場合は追加
                    if veh_id not in member_veh_ids_by_points[index]:
                        member_veh_ids_by_points[index].append(veh_id)
                        all_member_veh_ids.append(veh_id)

                    if end_mode:
                        pseud_change_info = (step, veh_id, index, times)
                        pseud_data.append(pseud_change_info)

            if virtual_vehicle_mode and veh_id in all_member_veh_ids and 'virtual' not in veh_id.split('_'):
                # 仮想車両を生成している車両がいるのであれば，その車両を取り除く
                if veh_id in virtual_veh_dict:
                    for virtual_veh_id in virtual_veh_dict[veh_id]:
                        traci.vehicle.remove(virtual_veh_id)
                        print('remove vehicle:', virtual_veh_id)
                    del virtual_veh_dict[veh_id]

                # 仮想車両生成
                for index, point in enumerate(candidate_points):
                    vehicles_in_point = len(member_veh_ids_by_points[index])
                    virtual_veh_ids = list()
                    # 対象の車両が対象領域の車両かつ車両台数が閾値以下かつ領域内の仮想車両台数が閾値いないの際
                    if veh_id in member_veh_ids_by_points[index] \
                            and vehicles_in_point < threshold \
                            and emitted_veh_num_by_points[index] < threshold - vehicles_in_point \
                            and vehicles_in_point != 0:
                        # 仮想車両生成台数を計算
                        emit_veh_num = int(math.ceil((threshold - vehicles_in_point) / vehicles_in_point))
                        print('emit_veh_num:', emit_veh_num)
                        # 指定分の仮想車両を生成
                        for i in range(emit_veh_num):
                            except_flag = False
                            virtual_veh_id = veh_id + '_virtual_' + str(step) + '_' + str(i)
                            try:
                                # veh_id, route_ id,type_id, depart, depart_lane, depart_pos,
                                # depart_speed, arrival_lane, arrival_pos, arrival_speed
                                traci.vehicle.add(virtual_veh_id, route_id, departPos='random_free', departSpeed=speed)
                                traci.vehicle.setRoute(virtual_veh_id, rest_routes)
                            except traci.TraCIException:
                                except_flag = True
                            if not except_flag:
                                print('add vehicle', virtual_veh_id)
                                virtual_veh_ids.append(virtual_veh_id)
                                emitted_veh_num_by_points[index] += 1

                        # 仮想車両のログを形成
                        virtual_veh_dict[veh_id] = virtual_veh_ids

            veh_data.append(veh_info)

        # シミュレーション時間の同期
        traci.simulationStep()
        step += 1

    traci.close()
    sys.stdout.flush()


# csvファイルを出力
def output_csv(filename, data):
    with open(filename, 'w') as f:
        writer = csv.writer(f)
        for row in data:
            writer.writerow(row)


# メインメソッド
if __name__ == "__main__":
    has_sumo_env()
    options = get_options()
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    traci.start([sumoBinary, "-c", target])
    run()

    output_csv('output/suggestion/{}/change_num_{}/threshold_{}/veh_data.csv'.format(schedule, change_pseudo_num, threshold), veh_data)
    output_csv('output/suggestion/{}/change_num_{}/threshold_{}/pseud_change.csv'.format(schedule, change_pseudo_num, threshold), pseud_data)
