__title__ = "VRMNXベンチマーク Ver.1.0b"
__author__ = "Caldia"
__update__  = "2022/09/10"
__eventUID__ = 1100002

import vrmapi
import shutil
import os.path
import subprocess
from datetime import datetime
from pathlib import Path

# ファイル読み込みの確認用
vrmapi.LOG("import " + __title__)

# main
def vrmevent(obj,ev,param):
    if ev == 'init':
        d = obj.GetDict()
        # フレームカウント
        obj.SetEventFrame()
        # 毎秒カウント
        d['bm_t_evid'] = obj.SetEventTimer(1.0, __eventUID__)
        # 秒間スコア
        d['bm_Score'] = 0
        # 現在スコア
        d['bm_NowScore'] = 0
        # 総合スコア
        d['bm_TotalScore'] = 0
        # 秒間スコアリスト
        d['bm_Graph'] = []
        # 最大最小平均
        d['bm_MaxScore'] = 0
        d['bm_MinScore'] = 999
        d['bm_AveScore'] = 0
        # 画面サイズ
        d['bm_DX'] = 0
        d['bm_DY'] = 0
        # ベンチマーク期間(秒)
        d['bm_Count'] = 60
        # ベンチマーク期間カウンター
        d['bm_CountNow'] = d['bm_Count']
        # dxdiagファイルが無ければ出力
        dir = vrmapi.SYSTEM().GetLayoutDir()
        if(os.path.exists(dir + "dxdiag.txt") == False):
            # 非同期実行
            subprocess.Popen(dir + "vrmnxbenchmark.bat")
    elif ev == 'timer' and param['eventUID'] == __eventUID__:
        d = obj.GetDict()
        # カウンター期間未満
        if len(d['bm_Graph']) < d['bm_Count']:
            # 秒間スコア表示
            d['bm_NowScore'] = d['bm_Score']
            # 大小比較
            if d['bm_Score'] > d['bm_MaxScore']:
                d['bm_MaxScore'] = d['bm_Score']
            if d['bm_Score'] < d['bm_MinScore']:
                d['bm_MinScore'] = d['bm_Score']
            # 秒間スコアリストに追加
            d['bm_Graph'].append(d['bm_Score'])
            # 秒間スコアをリセット
            d['bm_Score'] = 0
            d['bm_DX'] = int(vrmapi.SYSTEM().GetViewDX())
            d['bm_DY'] = int(vrmapi.SYSTEM().GetViewDY())
            # ベンチマーク期間カウンターを進める
            d['bm_CountNow'] = d['bm_CountNow'] - 1
        else:
            # イベントリセット
            obj.ResetEvent(d['bm_t_evid'])
            # ファイル出力
            writeScore(vrmapi.SYSTEM().GetLayoutDir(), d)
    elif ev == 'frame':
        d = obj.GetDict()
        g = vrmapi.ImGui()
        
        g.Begin('w1',__title__)
        # カウンター期間未満
        if len(d['bm_Graph']) < d['bm_Count']:
            # フレームスコア加算
            d['bm_Score'] = d['bm_Score'] + 1
            # トータルスコア加算
            d['bm_TotalScore'] = d['bm_TotalScore'] + 1
            # 表示
            g.Text("総合スコア：" + str(d['bm_TotalScore']))
            g.Text("現在：{}  最大：{}  最小：{}".format(d['bm_NowScore'], d['bm_MaxScore'], d['bm_MinScore']))
            g.Text("画面：{}×{}".format(d['bm_DX'], d['bm_DY']))
            g.Text("測定完了まであと" + str(d['bm_CountNow']) + "秒")
        else:
            # 終了表示
            d['bm_AveScore'] = int(d['bm_TotalScore'] / d['bm_Count'])
            g.Text("総合スコア：" + str(d['bm_TotalScore']))
            g.Text("平均：{}  最大：{}  最小：{}".format(d['bm_AveScore'], d['bm_MaxScore'], d['bm_MinScore']))
            g.Text("画面：{}×{}".format(d['bm_DX'], d['bm_DY']))
            g.Text("測定終了！")
            g.Text("[ESC]でビュワーを終了。")
        g.End()


# ファイル出力
def writeScore(path, d):
    s = ''
    # テンプレート読込み
    with open(path + "vrmnxbenchmark_template.html", encoding="utf-8") as f:
        s = f.read()

    # テンプレート置換
    s = s.replace('yyyy/MM/dd hh:mm', datetime.now().strftime('%Y/%m/%d %H:%M'))
    s = s.replace('DX×DY', "{}×{}".format(d['bm_DX'], d['bm_DY']))
    s = s.replace('TOTAL_SCORE', str(d['bm_TotalScore']))
    s = s.replace('AVE_SCORE', str(d['bm_AveScore']))
    s = s.replace('MAX_SCORE', str(d['bm_MaxScore']))
    s = s.replace('MIN_SCORE', str(d['bm_MinScore']))
    s = s.replace('総評', ScoreRank(d))
    s = s.replace('LAYOUT', os.path.basename(vrmapi.SYSTEM().GetLayoutPath()))

    # グラフ描画
    c = 0
    sl = list()
    sg = list()
    for l in d['bm_Graph']:
        sl.append('\'{}\', '.format(c))
        sg.append('{}, '.format(l))
        c = c + 1
    sl_text = ''.join(sl)
    sg_text = ''.join(sg)
    s = s.replace('\'0\', \'1\', \'2\', \'3\'', sl_text)
    s = s.replace('60, 60, 60, 60', sg_text)

    # dxdiag読込み
    dx_path = path + "dxdiag.txt"
    if(os.path.exists(dx_path) == True):
        with open(dx_path) as f:
            flist = f.readlines()
            for t in flist:
                if 'Operating System:' in t:
                    s = s.replace('                OS: N/A', t[7:-1].replace('Operating System:', '              OS:'))
                elif '  Processor:' in t:
                    s = s.replace('               CPU: N/A', t[7:-1].replace('Processor:', '      CPU:'))
                elif '  Memory:' in t:
                    s = s.replace('      メインメモリ: N/A', t[7:-1].replace('      Memory:', 'メインメモリ:'))
                elif '  Card name:' in t:
                    s = s.replace('               GPU: N/A', t[2:-1].replace('Card name:', '      GPU:'))
                elif '  Dedicated Memory:' in t:
                    s = s.replace('VRAM(ビデオメモリ): N/A', t[2:-1].replace('  Dedicated Memory:', 'VRAM(ビデオメモリ):'))
                elif '  Current Mode:' in t:
                    s = s.replace('ディスプレイ解像度: N/A', t[2:-1].replace('      Current Mode:', 'ディスプレイ解像度:'))
                elif 'DirectX Version:' in t:
                    s = s.replace('   DirectX Version: N/A', t[7:-1])

    # 結果出力
    timeText = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = path + "vrmnxbenchmark_" + timeText + ".html"
    with open(filename, mode='w', encoding="utf-8") as f:
        f.write(s)
    # 結果ブラウザ表示
    subprocess.Popen(filename, shell=True)


# 総評
def ScoreRank(d):
    if d['bm_AveScore'] < 10:
        return "Ｄランク：動かすことが厳しい環境です"
    elif d['bm_AveScore'] < 30:
        return "Ｃランク：遊ぶことが厳しい環境です"
    elif d['bm_AveScore'] < 60:
        return "Ｂランク：重たいですが遊ぶことができます"
    elif d['bm_AveScore'] < 90:
        return "Ａランク：快適に遊ぶことができます"
    elif d['bm_AveScore'] < 120:
        return "Ｓランク：非常に快適に遊ぶことができます！"
    else:
        return "SSランク：ゲーミングモニターで非常に快適に遊ぶことができます！！"
