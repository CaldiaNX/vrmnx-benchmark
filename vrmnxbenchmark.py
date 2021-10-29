__title__ = "VRMNXベンチマーク Ver.1.0"
__author__ = "Caldia"
__update__  = "2021/10/29"

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
        # フレームカウント
        obj.SetEventFrame()
        # 毎秒カウント
        obj.SetEventTimer(1.0, 101)
        d = obj.GetDict()
        # 秒間スコア
        d['score'] = 0
        # 現在スコア
        d['now_score'] = 0
        # 総合スコア
        d['total_score'] = 0
        # 秒間スコアリスト
        d['graph'] = []
        # 最大最小平均
        d['max_score'] = 0
        d['min_score'] = 999
        d['ave_score'] = 0
        # 画面サイズ
        d['dx'] = 0
        d['dy'] = 0
        # ベンチマーク期間(秒)
        d['count'] = 60
        # ベンチマーク期間カウンター
        d['count_now'] = d['count']
        # ファイル出力フラグ
        d['file_output'] = False
        # dxdiagファイル事前出力
        subprocess.Popen("dxdiag /t", shell=True)
    elif ev == 'timer':
        d = obj.GetDict()
        # カウンター期間未満
        if len(d['graph']) < d['count']:
            # 秒間スコア表示
            d['now_score'] = d['score']
            # 大小比較
            if d['score'] > d['max_score']:
                d['max_score'] = d['score']
            if d['score'] < d['min_score']:
                d['min_score'] = d['score']
            # 秒間スコアリストに追加
            d['graph'].append(d['score'])
            # 秒間スコアをリセット
            d['score'] = 0
            d['dx'] = int(vrmapi.SYSTEM().GetViewDX())
            d['dy'] = int(vrmapi.SYSTEM().GetViewDY())
            # ベンチマーク期間カウンターを進める
            d['count_now'] = d['count_now'] - 1
        else:
            # timerイベントをリセット
            obj.ResetEvent(101)
            # ファイル出力
            if d['file_output'] == False:
                # ResetEventエラー対策
                d['file_output'] = True
                writeScore(vrmapi.SYSTEM().GetLayoutDir(), d)
    elif ev == 'frame':
        d = obj.GetDict()
        g = vrmapi.ImGui()
        
        g.Begin('w1',__title__)
        # カウンター期間未満
        if len(d['graph']) < d['count']:
            # フレームスコア加算
            d['score'] = d['score'] + 1
            # トータルスコア加算
            d['total_score'] = d['total_score'] + 1
            # 表示
            g.Text("総合スコア：" + str(d['total_score']))
            g.Text("現在：{}  最大：{}  最小：{}".format(d['now_score'], d['max_score'], d['min_score']))
            g.Text("画面：{}×{}".format(d['dx'], d['dy']))
            g.Text("測定完了まであと" + str(d['count_now']) + "秒")
        else:
            # 終了表示
            d['ave_score'] = int(d['total_score'] / d['count'])
            g.Text("総合スコア：" + str(d['total_score']))
            g.Text("平均：{}  最大：{}  最小：{}".format(d['ave_score'], d['max_score'], d['min_score']))
            g.Text("画面：{}×{}".format(d['dx'], d['dy']))
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
    s = s.replace('DX×DY', "{}×{}".format(d['dx'], d['dy']))
    s = s.replace('TOTAL_SCORE', str(d['total_score']))
    s = s.replace('AVE_SCORE', str(d['ave_score']))
    s = s.replace('MAX_SCORE', str(d['max_score']))
    s = s.replace('MIN_SCORE', str(d['min_score']))
    s = s.replace('総評', ScoreRank(d))
    s = s.replace('LAYOUT', os.path.basename(vrmapi.SYSTEM().GetLayoutPath()))

    # グラフ描画
    c = 0
    sl = list()
    sg = list()
    for l in d['graph']:
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
                    s = s.replace('                  OS: N/A', t[5:-1])
                    s = s.replace('Operating System:', '              OS:')
                elif '  Processor:' in t:
                    s = s.replace('                 CPU: N/A', t[5:-1])
                    s = s.replace('Processor:', '      CPU:')
                elif '  Memory:' in t:
                    s = s.replace('        メインメモリ: N/A', t[5:-1])
                    s = s.replace('      Memory:', 'メインメモリ:')
                elif '  Card name:' in t:
                    s = s.replace('                 GPU: N/A', t[:-1])
                    s = s.replace('Card name:', '      GPU:')
                elif '  Dedicated Memory:' in t:
                    s = s.replace('  VRAM(ビデオメモリ): N/A', t[:-1])
                    s = s.replace('  Dedicated Memory:', 'VRAM(ビデオメモリ):')
                elif '  Current Mode:' in t:
                    s = s.replace('  ディスプレイ解像度: N/A', t[:-1])
                    s = s.replace('      Current Mode:', 'ディスプレイ解像度:')
                elif '  DirectX Version:' in t:
                    s = s.replace('     DirectX Version: N/A', t[5:-1])
    else:
        s = s.replace('                  OS: N/A\n', 'INFO］DirectX診断ツールを確認できませんでした。\n                  OS: N/A\n')

    # 結果出力
    timeText = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = path + "vrmnxbenchmark_" + timeText + ".html"
    with open(filename, mode='w', encoding="utf-8") as f:
        f.write(s)
    # 結果ブラウザ表示
    subprocess.Popen(filename, shell=True)

# 総評
def ScoreRank(d):
    if d['ave_score'] < 10:
        return "Ｄランク：動かすことが厳しい環境です"
    elif d['ave_score'] < 30:
        return "Ｃランク：遊ぶことが厳しい環境です"
    elif d['ave_score'] < 60:
        return "Ｂランク：重たいですが遊ぶことができます"
    elif d['ave_score'] < 90:
        return "Ａランク：快適に遊ぶことができます"
    elif d['ave_score'] < 120:
        return "Ｓランク：非常に快適に遊ぶことができます！"
    else:
        return "SSランク：ゲーミングモニターで非常に快適に遊ぶことができます！！"
