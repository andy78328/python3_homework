﻿import random, os
import math
import time 
import pygame
import copy
import argparse, socket, sys, pickle # 網路連線的部份額外添加的功能
from pygame.locals import *
from sys import exit
from chess import *

MAX_BYTES = 65535

#-*- coding: utf-8 -*-

background_image_filename = 'Image/SHEET.gif'
image_new        = 'Image/shield-and-swords.gif'

s_newgame = 'Sound/NEWGAME.WAV'
s_capture = 'Sound/CAPTURE2.WAV'
s_click   = 'Sound/CLICK.WAV'
s_loss    = 'Sound/LOSS.WAV'
s_move2   = 'Sound/MOVE2.WAV'
s_win     = 'Sound/WIN.WAV'

background = pygame.image.load(background_image_filename).convert()
new_game   = pygame.image.load(image_new).convert()

sound_new     = pygame.mixer.Sound(s_newgame)
sound_capture = pygame.mixer.Sound(s_capture)
sound_click   = pygame.mixer.Sound(s_click)
sound_loss    = pygame.mixer.Sound(s_loss)
sound_win     = pygame.mixer.Sound(s_win)
sound_move    = pygame.mixer.Sound(s_move2)

text_x = 237
text_y = 16
new_game_iconi = 440
new_game_iconj = 13

player_win = 0
player1_first = 0
first = 1
# turn_id, 0:black, 1:red, 2:process_moving
turn_id = 0
player2_color = 1
host_color = 0    # 代表本機遊戲玩家的顏色,如果玩家為player2,該顏色就會與player2相同,反之亦然
com_color = 1
max_value = 0
max_dist = 32
sindex = 0
#max_cor = None
open_score = None

#default chess
chtemp = chess(0, (0, 0), chess_back.get_size()) # 沒有座標,沒有實體的預設棋子

main_chess = [[chtemp, chtemp, chtemp, chtemp, chtemp, chtemp, chtemp, chtemp], [chtemp, chtemp, chtemp, chtemp, chtemp, chtemp, chtemp, chtemp], [chtemp, chtemp, chtemp, chtemp, chtemp, chtemp, chtemp, chtemp], [chtemp, chtemp, chtemp, chtemp, chtemp, chtemp, chtemp, chtemp]]
chess_index = [0] * 32
main_map = [[(0,0)]*8, [(0,0)]*8, [(0,0)]*8, [(0,0)]*8]
cor = [[(0,0)]*8, [(0,0)]*8, [(0,0)]*8, [(0,0)]*8]

mark = [[0]*8, [0]*8, [0]*8, [0]*8]
cannon_mark = [[0]*8, [0]*8, [0]*8, [0]*8]

king_live = [1, 1]
chess_num = [16, 16]
com_mv_map = [0, 0]
back_num = 32
com_will_eat_chess = []
will_eat_escape_chess = []
cannon_cor = []
break_long_capture_dest = []
break_long_capture_org = []
com_ban_step = []
move_step = [None, None, None, None]

def can_be_ate(small_value, big_value):       
    if 2 == big_value:
        return 0
    elif 1 == big_value and 7 == small_value:
        return 1
    elif 7 == big_value and 1 == small_value:
        return 0
    elif big_value > small_value:
        return 1
    else:
        return 0
    
def ini_random_chess(list):
    all_list = [0] * 32
    for end in range(31, -1, -1):
        start = random.randint(0, end)
        i = start
        while i != -1 :
            if 0 == all_list[start]:
                if i != 0:
                    start += 1
                    start %= 32
                    i -= 1
                else:
                    break
            else:
                start += 1
                start %= 32
        all_list[start] = 1
        list[31-end] = start
    return list

def findC(ch, x, y):
    for pr in ch:
        for p in pr:
            if math.hypot(p.x-x, p.y-y) <= p.size:
                return p
    return None

def all_chess_move(a_map, my_chess): # 可行的移動地點
    for chr in my_chess:
        for ch in chr:
            if ch.back < 1 and 1 == ch.live:
                ch.possible_move, a_map, my_chess= collect_possible_move(ch.row, ch.col, a_map, my_chess)
    return a_map, my_chess
    
def collect_possible_move(i, j, a_map, my_chess):
    
    pm = []
    ncor = near(i,j)
    for nc in ncor:
        if None == a_map[nc[0]][nc[1]]:
            pm.append(nc)
        elif a_map[i][j] != None: #a_map[i][j] != None and a_map[nc[0]][nc[1]] != None 
            if my_chess[a_map[nc[0]][nc[1]][0]][a_map[nc[0]][nc[1]][1]].color != my_chess[a_map[i][j][0]][a_map[i][j][1]].color and my_chess[a_map[nc[0]][nc[1]][0]][a_map[nc[0]][nc[1]][1]].back < 1:
                if 1 == my_chess[a_map[i][j][0]][a_map[i][j][1]].value and 7 == my_chess[a_map[nc[0]][nc[1]][0]][a_map[nc[0]][nc[1]][1]].value:
                    pm.append(nc)
                elif 7 == my_chess[a_map[i][j][0]][a_map[i][j][1]].value and 1 == my_chess[a_map[nc[0]][nc[1]][0]][a_map[nc[0]][nc[1]][1]].value:
                    pass
                elif my_chess[a_map[i][j][0]][a_map[i][j][1]].value != 2 and my_chess[a_map[i][j][0]][a_map[i][j][1]].value >= my_chess[a_map[nc[0]][nc[1]][0]][a_map[nc[0]][nc[1]][1]].value:
                    pm.append(nc)
    if a_map[i][j] != None:
        if 2 == my_chess[a_map[i][j][0]][a_map[i][j][1]].value:
            jump = 0
            for ii in range(i-1, -1, -1):
                if 1 == jump and a_map[ii][j] != None:
                    if 1 == my_chess[a_map[ii][j][0]][a_map[ii][j][1]].back or my_chess[a_map[ii][j][0]][a_map[ii][j][1]].color == my_chess[a_map[i][j][0]][a_map[i][j][1]].color:
                        break
                    else:
                        pm.append((ii, j))
                        break
                if a_map[ii][j] != None:
                    jump = 1
            jump = 0
            for ii in range(i+1, 4, 1):
                if 1 == jump and a_map[ii][j] != None:
                    if 1 == my_chess[a_map[ii][j][0]][a_map[ii][j][1]].back or my_chess[a_map[ii][j][0]][a_map[ii][j][1]].color == my_chess[a_map[i][j][0]][a_map[i][j][1]].color:
                        break
                    else:
                        pm.append((ii, j))
                        break
                if a_map[ii][j] != None:
                    jump = 1
            jump = 0
            for jj in range(j-1, -1, -1):
                if 1 == jump and a_map[i][jj] != None:
                    if 1 == my_chess[a_map[i][jj][0]][a_map[i][jj][1]].back or my_chess[a_map[i][jj][0]][a_map[i][jj][1]].color == my_chess[a_map[i][j][0]][a_map[i][j][1]].color:
                        break
                    else:
                        pm.append((i, jj))
                        break
                if a_map[i][jj] != None:
                    jump = 1
            jump = 0
            for jj in range(j+1, 8, 1):
                if 1 == jump and a_map[i][jj] != None:
                    if 1 == my_chess[a_map[i][jj][0]][a_map[i][jj][1]].back or my_chess[a_map[i][jj][0]][a_map[i][jj][1]].color == my_chess[a_map[i][j][0]][a_map[i][j][1]].color:
                        break
                    else:
                        pm.append((i, jj))
                        break
                if a_map[i][jj] != None:
                    jump = 1
    return pm, a_map, my_chess

def opp_cannon_can_eat(org, dest, my_chess, a_map):
    (i, j) = org
    (ii, jj) = dest
    o_color = my_chess[a_map[i][j][0]][a_map[i][j][1]].color
    ch1 = None
    ch2 = None
    if i == ii:
        for ki in range(ii+1, 4):
            if a_map[ki][jj] != None:
                (mi, mj) = a_map[ki][jj]
                ch1 = my_chess[mi][mj]
                break
        for ki in range(ii-1, -1, -1):
            if a_map[ki][jj] != None:
                (mi, mj) = a_map[ki][jj]
                ch2 = my_chess[mi][mj]
                break
        if ch1 != None and ch2 != None:
            if (ch1.color == o_color and ch2.color == 1 - o_color and ch1.back < 1 and ch2.back < 1 and ch2.value == 2) or (ch1.color == 1 - o_color and ch2.color == o_color and ch1.back < 1 and ch2.back < 1 and ch1.value == 2):
                return 1        
    else:       
        for kj in range(jj+1, 8):
            if a_map[ii][kj] != None:
                (mi, mj) = a_map[ii][kj]
                ch1 = my_chess[mi][mj]
                break
        for kj in range(jj-1, -1, -1):
            if a_map[ii][kj] != None:
                (mi, mj) = a_map[ii][kj]
                ch2 = my_chess[mi][mj]
                break
        if ch1 != None and ch2 != None:
            if (ch1.color == o_color and ch2.color == 1 - o_color and ch1.back < 1 and ch2.back < 1 and ch2.value == 2) or (ch1.color == 1 - o_color and ch2.color == o_color and ch1.back < 1 and ch2.back < 1 and ch1.value == 2):
                return 1
    return 0

def next_cannon_can_eat_more(org, dest, a_map, my_chess):
    global cannon_cor
    cannon_cor = []
    (i, j) = org
    n = a_map[i][j]
    if n == None:
        return 0
    nc = my_chess[n[0]][n[1]]
    
    was_ate = eat_by_bomb(org, a_map, my_chess)
    if was_ate == 0:
        return 0
    else:
        af_map = copy.deepcopy(a_map)
        af_ch = copy.deepcopy(my_chess)
        if org != None and dest != None:
            af_map, af_ch = move(org, dest, af_map, af_ch)
            af_map, af_ch = all_chess_move(af_map, af_ch)
            
            for cc in cannon_cor:
                afm = af_map[cc[0]][cc[1]]
                if afm != None:
                    afc = af_ch[afm[0]][afm[1]]
                    for fcp in afc.possible_move:
                        (pi, pj) = fcp
                        c = af_map[pi][pj]
                        if c != None and (pi == i or pj == j):
                            ch = af_ch[c[0]][c[1]]
                            if  eating_value_to_score(ch.value, king_live, ch.color) > eating_value_to_score(nc.value, king_live, nc.color):
                                return 1
    return 0                                
    
def eat_by_bomb(org, a_map, my_chess):
    global cannon_cor
    (i, j) = org
    jump = 0
    was_ate = 0
    for ii in range(i-1, -1, -1):
        if 1 == jump and a_map[ii][j] != None:
            if 1 == my_chess[a_map[ii][j][0]][a_map[ii][j][1]].back or my_chess[a_map[ii][j][0]][a_map[ii][j][1]].color == my_chess[a_map[i][j][0]][a_map[i][j][1]].color:
                break
            elif 2 == my_chess[a_map[ii][j][0]][a_map[ii][j][1]].value:
                cannon_cor.append((ii,j))
                was_ate = 1
                break
        elif a_map[ii][j] != None:
            jump = 1
    jump = 0
    for ii in range(i+1, 4, 1):
        if 1 == jump and a_map[ii][j] != None:
            if 1 == my_chess[a_map[ii][j][0]][a_map[ii][j][1]].back or my_chess[a_map[ii][j][0]][a_map[ii][j][1]].color == my_chess[a_map[i][j][0]][a_map[i][j][1]].color:
                break
            elif 2 == my_chess[a_map[ii][j][0]][a_map[ii][j][1]].value:
                cannon_cor.append((ii,j))
                was_ate = 1
                break
        elif a_map[ii][j] != None:
            jump = 1
    jump = 0
    for jj in range(j-1, -1, -1):
        if 1 == jump and a_map[i][jj] != None:
            if 1 == my_chess[a_map[i][jj][0]][a_map[i][jj][1]].back or my_chess[a_map[i][jj][0]][a_map[i][jj][1]].color == my_chess[a_map[i][j][0]][a_map[i][j][1]].color:
                break
            elif 2 == my_chess[a_map[i][jj][0]][a_map[i][jj][1]].value:
                cannon_cor.append((i,jj))
                was_ate = 1
                break
        elif a_map[i][jj] != None:
            jump = 1
    jump = 0
    for jj in range(j+1, 8, 1):
        if 1 == jump and a_map[i][jj] != None:
            if 1 == my_chess[a_map[i][jj][0]][a_map[i][jj][1]].back or my_chess[a_map[i][jj][0]][a_map[i][jj][1]].color == my_chess[a_map[i][j][0]][a_map[i][j][1]].color:
                break
            elif 2 == my_chess[a_map[i][jj][0]][a_map[i][jj][1]].value:
                cannon_cor.append((i,jj))
                was_ate = 1
                break
        elif a_map[i][jj] != None:
            jump = 1
    return was_ate
    
def eat_by_bomb_not_check_color(org, a_map, my_chess):
    global cannon_cor
    (i, j) = org
    jump = 0
    was_ate = 0
    for ii in range(i-1, -1, -1):
        if 1 == jump and a_map[ii][j] != None:
            if 1 == my_chess[a_map[ii][j][0]][a_map[ii][j][1]].back:
                break
            elif 2 == my_chess[a_map[ii][j][0]][a_map[ii][j][1]].value:
                cannon_cor.append((ii,j))
                was_ate = 1
                break
        elif a_map[ii][j] != None:
            jump = 1
    jump = 0
    for ii in range(i+1, 4, 1):
        if 1 == jump and a_map[ii][j] != None:
            if 1 == my_chess[a_map[ii][j][0]][a_map[ii][j][1]].back:
                break
            elif 2 == my_chess[a_map[ii][j][0]][a_map[ii][j][1]].value:
                cannon_cor.append((ii,j))
                was_ate = 1
                break
        elif a_map[ii][j] != None:
            jump = 1
    jump = 0
    for jj in range(j-1, -1, -1):
        if 1 == jump and a_map[i][jj] != None:
            if 1 == my_chess[a_map[i][jj][0]][a_map[i][jj][1]].back:
                break
            elif 2 == my_chess[a_map[i][jj][0]][a_map[i][jj][1]].value:
                cannon_cor.append((i,jj))
                was_ate = 1
                break
        elif a_map[i][jj] != None:
            jump = 1
    jump = 0
    for jj in range(j+1, 8, 1):
        if 1 == jump and a_map[i][jj] != None:
            if 1 == my_chess[a_map[i][jj][0]][a_map[i][jj][1]].back:
                break
            elif 2 == my_chess[a_map[i][jj][0]][a_map[i][jj][1]].value:
                cannon_cor.append((i,jj))
                was_ate = 1
                break
        elif a_map[i][jj] != None:
            jump = 1
    return was_ate
    
def near(i, j):
    n_cor = []
    if 0 == i and 0 == j:
        n_cor.extend([(1,0), (0,1)])
    elif 3 == i and 0 == j:
        n_cor.extend([(2, 0), (3, 1)])
    elif 0 == i and 7 == j:
        n_cor.extend([(0, 6), (1, 7)])
    elif 3 == i and 7 == j:
        n_cor.extend([(3, 6), (2, 7)])
    elif 0 == j:
        n_cor.extend([(i-1, j), (i+1, j), (i, j+1)])
    elif 0 == i:
        n_cor.extend([(i, j-1), (i, j+1), (i+1, j)])
    elif 7 == j:
        n_cor.extend([(i-1, j), (i+1, j), (i, j-1)])
    elif 3 == i:
        n_cor.extend([(i, j-1), (i, j+1), (i-1, j)])
    else:
        n_cor.extend([(i-1, j), (i+1, j), (i, j+1), (i, j-1)])
    
    return n_cor
    
def mouse_position_to_block(mx, my, chess_back):
    global cstart_x
    global cstart_y
    global cstart_x2
    global cstart_y2
    
    for i in range(0, 4):
        for j in range(0, 4):
            if cstart_x+j*chess_back.get_width() < mx < cstart_x+(j+1)*chess_back.get_width() and cstart_y+i*chess_back.get_height() < my < cstart_y+(i+1)*chess_back.get_height():
                return (i, j)
        
    for i in range(0, 4):
        for j in range(0, 4):
            if cstart_x2+j*chess_back.get_width() < mx < cstart_x2+(j+1)*chess_back.get_width() and cstart_y2+i*chess_back.get_height() < my < cstart_y2+(i+1)*chess_back.get_height():
                return (i, 4+j)

def near_max_value(open, org, a_map, my_chess):
    if None == open:
        return None
    (y, x) = open
    near_cor = near(y, x)
    max = 0
    for kk in near_cor:
        if kk == org:
            continue
        else:
            (ni, nj) = kk
            if a_map[ni][nj] != None:
                an = a_map[ni][nj]
                if my_chess[an[0]][an[1]].live == 1 and my_chess[an[0]][an[1]].back < 1:
                    if my_chess[an[0]][an[1]].color == com_color:
                        continue
                    if my_chess[an[0]][an[1]].value > max:
                        max = my_chess[an[0]][an[1]].value
    return max

def near_max_value_not_consider_com_color(open, org, a_map, my_chess):
    if None == open:
        return None
    (y, x) = open
    near_cor = near(y, x)
    max = 0
    for kk in near_cor:
        if kk == org:
            continue
        else:
            (ni, nj) = kk
            if a_map[ni][nj] != None:
                an = a_map[ni][nj]
                if my_chess[an[0]][an[1]].live == 1 and my_chess[an[0]][an[1]].back < 1:
                    #if my_chess[an[0]][an[1]].color == com_color:
                    #    continue
                    if my_chess[an[0]][an[1]].value > max:
                        max = my_chess[an[0]][an[1]].value
    return max    
    
def scan_player_bomb(a_map, my_chess):
    for cr in my_chess:
        for c in cr:
            if 1 == c.live and c.back < 1 and 2 == c.value and player_color == c.color:
                near_cor = near(c.row, c.col)
                i = random.randint(0, len(near_cor)-1)
                for ii in range(0, len(near_cor)):
                    n = (i+ii)%len(near_cor)
                    (ni, nj) = near_cor[n]
                    an = a_map[ni][nj]
                    if None == an:
                        continue
                    elif 0 == my_chess[an[0]][an[1]].live or my_chess[an[0]][an[1]].back < 1:
                        continue
                    if near_max_value(near_cor[n], (c.row, c.col), a_map, my_chess) <= 3:
                        return near_cor[n]
    return None

def scan_com_second_big(a_map, my_chess):
    for cr in my_chess:
        for c in cr:
            if 1 == c.live and c.back < 1 and 6 == c.value and com_color == c.color:
                near_cor = near(c.row, c.col)
                i = random.randint(0, len(near_cor)-1)
                for ii in range(0, len(near_cor)):
                    n = (i+ii)%len(near_cor)
                    (ni, nj) = near_cor[n]
                    an = a_map[ni][nj]
                    if None == an:
                        continue
                    elif 0 == my_chess[an[0]][an[1]].live or my_chess[an[0]][an[1]].back < 1:
                        continue
                    if near_max_value(near_cor[n], (c.row, c.col), a_map, my_chess) <= 5:
                        return near_cor[n]
    return None

def bomb_will_eat(org, a_map, my_chess):
    if None == org:
        return None
    i = random.randint(0, 3)
    
    for i2 in range(0, 4):
        n = (i+i2)%4
        (ni, nj) = org
        if 0 == n:
            jump = 0
            for ii in range(ni-1, -1, -1):
                if 1 == jump and a_map[ii][nj] != None:
                    an = a_map[ii][nj]
                    if my_chess[an[0]][an[1]].back < 1 and my_chess[an[0]][an[1]].color == player_color:
                        if near_max_value((ii, nj), None, a_map, my_chess) < 2:
                            return org
                    break
                if a_map[ii][nj] != None:
                    bn = a_map[ii][nj]
                    if 1 == my_chess[bn[0]][bn[1]].back:
                        jump = 1
                    else:
                        break
        elif 1 == n:
            jump = 0
            for ii in range(ni+1, 4, 1):
                if 1 == jump and a_map[ii][nj] != None:
                    an = a_map[ii][nj]
                    if my_chess[an[0]][an[1]].back < 1 and my_chess[an[0]][an[1]].color == player_color:
                        if near_max_value((ii, nj), None, a_map, my_chess) < 2:
                            return org
                    break
                if a_map[ii][nj] != None:
                    bn = a_map[ii][nj]
                    if 1 == my_chess[bn[0]][bn[1]].back:
                        jump = 1
                    else:
                        break
        elif 2 == n:
            jump = 0
            for jj in range(nj-1, -1, -1):
                if 1 == jump and a_map[ni][jj] != None:
                    an = a_map[ni][jj]
                    if my_chess[an[0]][an[1]].back < 1 and my_chess[an[0]][an[1]].color == player_color:
                        if near_max_value((ni, jj), None, a_map, my_chess) < 2:
                            return org
                    break
                if a_map[ni][jj] != None:
                    bn = a_map[ni][jj]
                    if 1 == my_chess[bn[0]][bn[1]].back:
                        jump = 1
                    else:
                        break
        elif 3 == n:
            jump = 0
            for jj in range(nj+1, 8, 1):
                if 1 == jump and a_map[ni][jj] != None:
                    an = a_map[ni][jj]
                    if my_chess[an[0]][an[1]].back < 1 and my_chess[an[0]][an[1]].color == player_color:
                        if near_max_value((ni, jj), None, a_map, my_chess) < 2:
                            return org
                    break
                if a_map[ni][jj] != None:
                    bn = a_map[ni][jj]
                    if 1 == my_chess[bn[0]][bn[1]].back:
                        jump = 1
                    else:
                        break
    return None    
    
def bomb_may_eat(org, a_map, my_chess):
    if None == org:
        return None
    i = random.randint(0, 3)
    
    for i2 in range(0, 4):
        n = (i+i2)%4
        (ni, nj) = org
        if 0 == n:
            jump = 0
            for ii in range(ni-1, -1, -1):
                if 1 == jump and a_map[ii][nj] != None:
                    an = a_map[ii][nj]
                    if 1 == my_chess[an[0]][an[1]].back:
                        if near_max_value_not_consider_com_color((ii, nj), None, a_map, my_chess) < 2:
                            return (ii, nj)
                    break
                if a_map[ii][nj] != None:
                    bn = a_map[ii][nj]
                    if 1 == my_chess[bn[0]][bn[1]].back:
                        jump = 1
                    else:
                        break
        elif 1 == n:
            jump = 0
            for ii in range(ni+1, 4, 1):
                if 1 == jump and a_map[ii][nj] != None:
                    an = a_map[ii][nj]
                    if 1 == my_chess[an[0]][an[1]].back:
                        if near_max_value_not_consider_com_color((ii, nj), None, a_map, my_chess) < 2:
                            return (ii, nj)
                    break
                if a_map[ii][nj] != None:
                    bn = a_map[ii][nj]
                    if 1 == my_chess[bn[0]][bn[1]].back:
                        jump = 1
                    else:
                        break
        elif 2 == n:
            jump = 0
            for jj in range(nj-1, -1, -1):
                if 1 == jump and a_map[ni][jj] != None:
                    an = a_map[ni][jj]
                    if 1 == my_chess[an[0]][an[1]].back:
                        if near_max_value_not_consider_com_color((ni, jj), None, a_map, my_chess) < 2:
                            return (ni, jj)
                    break
                if a_map[ni][jj] != None:
                    bn = a_map[ni][jj]
                    if 1 == my_chess[bn[0]][bn[1]].back:
                        jump = 1
                    else:
                        break
        elif 3 == n:
            jump = 0
            for jj in range(nj+1, 8, 1):
                if 1 == jump and a_map[ni][jj] != None:
                    an = a_map[ni][jj]
                    if 1 == my_chess[an[0]][an[1]].back:
                        if near_max_value_not_consider_com_color((ni, jj), None, a_map, my_chess) < 2:
                            return (ni, jj)
                    break
                if a_map[ni][jj] != None:
                    bn = a_map[ni][jj]
                    if 1 == my_chess[bn[0]][bn[1]].back:
                        jump = 1
                    else:
                        break
    return None
    
def scan_com_bomb(a_map, my_chess):
    cor = None
    for cr in my_chess:
        for c in cr:
            if 1 == c.live and c.back < 1 and 2 == c.value and com_color == c.color:
                cor = bomb_may_eat((c.row, c.col), a_map, my_chess)
    return cor

#def scan_open_bomb(a_map, my_chess):
#    cor = None
#    for s_num in range(0, 32):
#        s = random.randint(0, 31)
#        j = s/4
#        i = s%4
#        a = a_map[i][j]
#        if None == a:
#            continue
#        m = my_chess[a[0]][a[1]]
#        if m.back < 1 or 0 == m.live:
#            continue
#        cor = bomb_will_eat((i,j), a_map, my_chess)
#        if None == cor:
#            continue
#        ncor = near(a[0], a[1])
#        for nc in ncor:
#            b = a_map[nc[0]][nc[1]]
#            if None == b:
#                continue
#            mn = my_chess[b[0]][b[1]]
#            if 0 == mn.live or None == mn:
#                continue
#            if mn.back < 1:
#                if mn.color == player_color and mn.value > 2:
#                    cor = None
#                    break
#        if cor != None:
#            return cor
#    return cor
    
def select_back_chess(a_map, my_chess, org = None):
    global back_num
    
    back_mark = [[0]*8, [0]*8, [0]*8, [0]*8]
    (i, j) = (None, None)
    
    # temp
    print '0'
    
    cor = scan_player_bomb(a_map, my_chess)
    if cor != None:
        return cor
    
    # temp
    print '1'
    
    cor = scan_com_bomb(a_map, my_chess)
    if cor != None:
        return cor
    
    # temp
    print '2'
    
    if back_num > 6:
        cor = scan_com_second_big(a_map, my_chess)
        if cor != None:
            return cor
    
    # temp
    print '3'
    
    for k in range(0, 32):
        if 1 == check_back_exist(a_map, my_chess, back_mark):
            (y, x) = random_select_back_chess(a_map, my_chess, back_mark)
            if 0 == eat_by_bomb_not_check_color((y, x), a_map, my_chess):
                near_cor = near(y, x)
                n = 0
                for kk in near_cor:
                    (ni, nj) = kk
                    if a_map[ni][nj] != None:
                        an = a_map[ni][nj]
                        if my_chess[an[0]][an[1]].back < 1:
                            n = 1
                            break
                if 0 == n:
                    (i, j) = (y, x)
                else:
                    back_mark[y][x] = 1
            else:
                back_mark[y][x] = 1
        else:
            break
    if (i, j) != (None, None):
        return (i, j)
    elif org != None:
        #  (-1, -1) to move a piece
        return (-1, -1)
    else:
        back_mark = [[0]*8, [0]*8, [0]*8, [0]*8]
        if 1 == check_back_exist(a_map, my_chess, back_mark):
            return random_select_back_chess(a_map, my_chess, back_mark)
        else:
            return None

def check_back_exist(a_map, my_chess, bm):
    back_exist = 0
    for i in range(0, 4):
        for j in range(0, 8):
            if a_map[i][j] != None and bm[i][j] != 1:
                if 1 == my_chess[a_map[i][j][0]][a_map[i][j][1]].back:
                    back_exist = 1
    return back_exist
    
def random_select_back_chess(a_map, my_chess, bm):    
    i = random.randint(0, 31)
    ii = 0
    
    while i != -1:
        y = ii/8
        x = ii%8
        if a_map[y][x] == None or bm[y][x] == 1:
            ii += 1
            if ii > 31:
                ii = 0
        elif 1 == my_chess[a_map[y][x][0]][a_map[y][x][1]].back:
            i -= 1
            if i < 0:
                break
            ii += 1
            if ii > 31:
                ii = 0
        else:
            ii += 1
            if ii > 31:
                ii = 0
    
    return (y, x)
                
def chess_ai():
    global turn_id
    global first
    global main_chess
    global main_map
    global player_color
    global com_color
    global player1_first
    global player_win
    global back_num
    global com_will_eat_chess
    global will_eat_escape_chess 
    
    pygame.display.update()
    
    if 0 == player1_first and  1 == first:
        i = random.randint(0, 3) 
        j = random.randint(0, 7) 
        turn_id = main_chess[i][j].color
        main_chess[i][j].back = -1
        back_num -= 1
        com_color = turn_id
        player_color = 1 - com_color
        first = 0
    elif turn_id == com_color and 0 == first:
        com_will_eat_chess = []
        will_eat_escape_chess = [] 
        main_chess = clean_back_n1_to_0(main_chess)
        
        move_pre1 = move_step[(sindex-1)%4] # player
        move_pre2 = move_step[(sindex-2)%4] # com
        move_pre3 = move_step[(sindex-3)%4] # player
        move_pre4 = move_step[sindex]       # com
                
        if move_pre1 != None and move_pre2 != None and move_pre3 != None and move_pre4 != None:
            # print 'map 1=', main_map[move_pre1[2][0]][move_pre1[2][1]]
            # print 'chess 1=', main_chess[main_map[move_pre1[2][0]][move_pre1[2][1]][0]][main_map[move_pre1[2][0]][move_pre1[2][1]][1]].value
            
            # print 'map 2=', main_map[move_pre2[2][0]][move_pre2[2][1]]
            # print 'chess 2=', main_chess[main_map[move_pre2[2][0]][move_pre2[2][1]][0]][main_map[move_pre2[2][0]][move_pre2[2][1]][1]].value
            
            if move_pre1[0] == player_color and move_pre2[0] == com_color and move_pre3[0] == player_color and move_pre4[0] == com_color and 1 == can_be_ate(main_chess[main_map[move_pre1[2][0]][move_pre1[2][1]][0]][main_map[move_pre1[2][0]][move_pre1[2][1]][1]].value, main_chess[main_map[move_pre2[2][0]][move_pre2[2][1]][0]][main_map[move_pre2[2][0]][move_pre2[2][1]][1]].value) and move_pre2[2] == move_pre4[1] and move_pre1[2] == move_pre3[1]:
                n1 = move_pre1[1]
                n2 = move_pre2[1]
                p  = move_pre1[2]
                c  = move_pre2[2]
                if None == main_map[n1[0]][n1[1]] and None == main_map[n2[0]][n2[1]] and 1 == abs(p[0]-n1[0]) + abs(p[1]-n1[1]) and 1 == abs(p[0]-n2[0]) + abs(p[1]-n2[1]):
                    break_long_capture_dest.append([n1, n2, p, c])
                    break_long_capture_org.append([p, c])
                    com_ban_step.append(move_pre4[1])
                    print 'long capture'
        
        org, dest, score = com_think(main_map, main_chess)
        print 'org', org, 'dest', dest, 'score', score, 'op score', open_score
                            
        if 0 == back_num and 1 == cant_move(main_map, main_chess, com_color):
            player_win = 1
        if back_num > 0:
            if open_score != None:
                r = random.randint(1, 9)
                if None == org:
                    dest = select_back_chess(main_map, main_chess)
                    sound_click.play()
                    main_chess[main_map[dest[0]][dest[1]][0]][main_map[dest[0]][dest[1]][1]].back = -1
                    back_num -= 1
                elif score > open_score - (float)(r)/10:
                    if score > 18:
                        org = None
                    temp = select_back_chess(main_map, main_chess, org)
                    if (-1, -1) == temp:
                        main_map, main_chess = move_s(org, dest, main_map, main_chess)
                        save_step_and_break_long_capture(org, dest)
                    else:
                        sound_click.play()
                        main_chess[main_map[temp[0]][temp[1]][0]][main_map[temp[0]][temp[1]][1]].back = -1
                        back_num -= 1 
                elif score == open_score:
                    if score >= 0:
                        if score > 18:
                            org = None
                        temp = select_back_chess(main_map, main_chess, org)
                        if (-1, -1) == temp:
                            main_map, main_chess = move_s(org, dest, main_map, main_chess)
                            save_step_and_break_long_capture(org, dest)
                        else:
                            sound_click.play()
                            main_chess[main_map[temp[0]][temp[1]][0]][main_map[temp[0]][temp[1]][1]].back = -1
                            back_num -= 1
                    else:
                        main_map, main_chess = move_s(org, dest, main_map, main_chess)
                        save_step_and_break_long_capture(org, dest)
                else:
                    main_map, main_chess = move_s(org, dest, main_map, main_chess)
                    save_step_and_break_long_capture(org, dest)
            else:
                main_map, main_chess = move_s(org, dest, main_map, main_chess)
                save_step_and_break_long_capture(org, dest)
        elif 0 == player_win:
            main_map, main_chess = move_s(org, dest, main_map, main_chess)
            save_step_and_break_long_capture(org, dest)
   
    if turn_id == com_color:
        turn_id = 2
        
def short_dist(i, j, dist, a_map):
    d = 0
    ncor = near(i, j)
    for nc in ncor:
        if mark[nc[0]][nc[1]] != 0 and mark[nc[0]][nc[1]] < dist:
            if 0 == d:
                d = mark[nc[0]][nc[1]]+1
            elif mark[nc[0]][nc[1]]+1 < d:
                d = mark[nc[0]][nc[1]]+1
    
    if 0 == d and None == a_map[i][j]:
        d = dist
    
    return d
        
        
def move_max_value(orgx, orgy, destx, desty, my_chess, a_map, org_value, owner_color, i, j, dist=1):
    global max_value
    global mark
    #global max_cor
    global cannon_mark
    global max_dist
    
    if i == -1 or j == -1 or i == 4 or j == 8:
        return
    elif i == orgy and j == orgx:
        return
    #elif 1 == mark[i][j]:
    elif mark[i][j] > 0 or cannon_mark[i][j] > 0:
        return
    elif a_map[i][j] != None:
        if 1 == my_chess[a_map[i][j][0]][a_map[i][j][1]].back:
            return
        #elif owner_color == my_chess[a_map[i][j][0]][a_map[i][j][1]].color:
        #    return
    
    opp_color = 1 - owner_color
    current_dist = 32
    
    if  a_map[i][j] != None:
        current_dist = short_dist(i, j, dist, a_map)
    else:
        mark[i][j] = short_dist(i, j, dist, a_map)
    
    if a_map[i][j] != None:
        if opp_color == my_chess[a_map[i][j][0]][a_map[i][j][1]].color:
            if 7 == org_value:
                if 1 == my_chess[a_map[i][j][0]][a_map[i][j][1]].value:
                    #max_value = 8
                    #max_cor = (i, j)
                    return
                elif 2 == my_chess[a_map[i][j][0]][a_map[i][j][1]].value and max_value <= 5.5:
                    if max_value < 5.5:
                        max_value = 5.5
                        max_dist = current_dist
                    elif current_dist < max_dist:
                        max_dist = current_dist
                    return
                elif max_value <= my_chess[a_map[i][j][0]][a_map[i][j][1]].value:
                    if max_value < my_chess[a_map[i][j][0]][a_map[i][j][1]].value:
                        max_value = my_chess[a_map[i][j][0]][a_map[i][j][1]].value
                        max_dist = current_dist
                    #max_cor = (i, j)
                    elif current_dist < max_dist:
                        max_dist = current_dist
                    return
            elif 1 == org_value:
                #print 'max_value', max_value
                if 7 == my_chess[a_map[i][j][0]][a_map[i][j][1]].value:
                    if max_value != 9:
                        max_value = 9
                        max_dist = current_dist
                    #max_cor = (i, j)
                    elif current_dist < max_dist:
                        max_dist = current_dist
                    return
                elif my_chess[a_map[i][j][0]][a_map[i][j][1]].value == 1:
                    if max_value != 1:
                        max_value = 1
                        max_dist = current_dist
                    #max_cor = (i, j)
                    elif current_dist < max_dist:
                        max_dist = current_dist
                    return
            elif 2 == my_chess[a_map[i][j][0]][a_map[i][j][1]].value and org_value > 2 and max_value <= 5.5:
                if max_value < 5.5:
                    max_value = 5.5
                    max_dist = current_dist
                elif current_dist < max_dist:
                    max_dist = current_dist
                return
            elif max_value <= my_chess[a_map[i][j][0]][a_map[i][j][1]].value and my_chess[a_map[i][j][0]][a_map[i][j][1]].value <= org_value:
                if max_value < my_chess[a_map[i][j][0]][a_map[i][j][1]].value:
                    max_value = my_chess[a_map[i][j][0]][a_map[i][j][1]].value
                    max_dist = current_dist
                #max_cor = (i, j)
                elif current_dist < max_dist:
                    max_dist = current_dist
                return
    elif orgy == desty and orgx+1 == destx:
        #print 'org_value', org_value, 'max_value', max_value, 'i=', i, 'j=', j, 'dist=', dist, 'mark[i][j]=', mark[i][j]
        move_max_value(orgx, orgy, destx, desty, my_chess, a_map, org_value, owner_color, i, j+1, dist+1)
        move_max_value(orgx, orgy, destx, desty, my_chess, a_map, org_value, owner_color, i, j-1, dist+1)
        move_max_value(orgx, orgy, destx, desty, my_chess, a_map, org_value, owner_color, i+1, j, dist+1)
        move_max_value(orgx, orgy, destx, desty, my_chess, a_map, org_value, owner_color, i-1, j, dist+1)   
    elif orgy == desty and orgx-1 == destx:
        #print 'org_value', org_value, 'max_value', max_value, 'i=', i, 'j=', j, 'dist=', dist, 'mark[i][j]=', mark[i][j]
        move_max_value(orgx, orgy, destx, desty, my_chess, a_map, org_value, owner_color, i, j-1, dist+1)
        move_max_value(orgx, orgy, destx, desty, my_chess, a_map, org_value, owner_color, i, j+1, dist+1)
        move_max_value(orgx, orgy, destx, desty, my_chess, a_map, org_value, owner_color, i+1, j, dist+1)
        move_max_value(orgx, orgy, destx, desty, my_chess, a_map, org_value, owner_color, i-1, j, dist+1)
    elif orgy+1 == desty and orgx == destx:
        #print 'org_value', org_value, 'max_value', max_value, 'i=', i, 'j=', j, 'dist=', dist, 'mark[i][j]=', mark[i][j]
        move_max_value(orgx, orgy, destx, desty, my_chess, a_map, org_value, owner_color, i+1, j, dist+1)
        move_max_value(orgx, orgy, destx, desty, my_chess, a_map, org_value, owner_color, i-1, j, dist+1)
        move_max_value(orgx, orgy, destx, desty, my_chess, a_map, org_value, owner_color, i, j+1, dist+1)
        move_max_value(orgx, orgy, destx, desty, my_chess, a_map, org_value, owner_color, i, j-1, dist+1)
    elif orgy-1 == desty and orgx == destx:
        #print 'org_value', org_value, 'max_value', max_value, 'i=', i, 'j=', j, 'dist=', dist, 'mark[i][j]=', mark[i][j]
        move_max_value(orgx, orgy, destx, desty, my_chess, a_map, org_value, owner_color, i-1, j, dist+1)
        move_max_value(orgx, orgy, destx, desty, my_chess, a_map, org_value, owner_color, i+1, j, dist+1)
        move_max_value(orgx, orgy, destx, desty, my_chess, a_map, org_value, owner_color, i, j+1, dist+1)
        move_max_value(orgx, orgy, destx, desty, my_chess, a_map, org_value, owner_color, i, j-1, dist+1)
                
def caca(org, dest, my_chess, a_map, owner_color):        
    if org == None:
        return 0
    elif owner_color == player_color:
        return 0
    
    (orgy, orgx) = org
    (desty, destx) = dest
    
    m = a_map[orgy][orgx]
    if m == None:
        return 0
    elif 2 == my_chess[m[0]][m[1]].value:
        return 0
    
    if desty-1 >= 0 and destx-1 >=0:
        n = a_map[desty-1][destx-1]
        if n == None:
            pass
        else:
            mc = my_chess[n[0]][n[1]]
            if 0 == mc.live or 1 == mc.back:
                pass
            elif 7 == my_chess[m[0]][m[1]].value and 1 == my_chess[n[0]][n[1]].value and my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color:
                pass 
            elif my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color and my_chess[n[0]][n[1]].value == my_chess[m[0]][m[1]].value:
                return 1
            #elif 1 == my_chess[m[0]][m[1]].value and 7 == my_chess[n[0]][n[1]].value and my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color:
            #    return 1
    if desty-1 >= 0 and destx+1 <=7:
        n = a_map[desty-1][destx+1]
        if n == None:
            pass
        else:
            mc = my_chess[n[0]][n[1]]
            if 0 == mc.live or 1 == mc.back:
                pass
            elif 7 == my_chess[m[0]][m[1]].value and 1 == my_chess[n[0]][n[1]].value and my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color:
                pass
            elif my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color and my_chess[n[0]][n[1]].value == my_chess[m[0]][m[1]].value:
                return 1
            #elif 1 == my_chess[m[0]][m[1]].value and 7 == my_chess[n[0]][n[1]].value and my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color:
            #    return 1
    if desty+1 <= 3 and destx-1 >= 0:
        n = a_map[desty+1][destx-1]
        if n == None:
            pass
        else:
            mc = my_chess[n[0]][n[1]]
            if 0 == mc.live or 1 == mc.back:
                pass
            elif 7 == my_chess[m[0]][m[1]].value and 1 == my_chess[n[0]][n[1]].value and my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color:
                pass
            elif my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color and my_chess[n[0]][n[1]].value == my_chess[m[0]][m[1]].value:
                return 1
            #elif 1 == my_chess[m[0]][m[1]].value and 7 == my_chess[n[0]][n[1]].value and my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color:
            #    return 1
    if desty+1 <= 3 and destx+1 <= 7:
        n = a_map[desty+1][destx+1]
        if n == None:
            pass
        else:
            mc = my_chess[n[0]][n[1]]
            if 0 == mc.live or 1 == mc.back:
                pass
            elif 7 == my_chess[m[0]][m[1]].value and 1 == my_chess[n[0]][n[1]].value and my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color:
                pass
            elif my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color and my_chess[n[0]][n[1]].value == my_chess[m[0]][m[1]].value:
                return 1
            #elif 1 == my_chess[m[0]][m[1]].value and 7 == my_chess[n[0]][n[1]].value and my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color:
            #    return 1
    return 0
        
        
def near2_have_same_value(org, my_chess, a_map, owner_color):
    if org == None:
        return 0
    elif owner_color == player_color:
        return 0
    
    (orgy, orgx) = org
    
    m = a_map[orgy][orgx]
    if m == None:
        return 0
    elif 2 == my_chess[m[0]][m[1]].value:
        return 0
    
    if orgy-2 >= 0:
        n = a_map[orgy-2][orgx]
        if n == None:
            pass
        else:
            mc = my_chess[n[0]][n[1]]
            if 0 == mc.live or 1 == mc.back:
                pass
            elif 7 == my_chess[m[0]][m[1]].value and 1 == my_chess[n[0]][n[1]].value and my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color:
                pass
            elif my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color and my_chess[n[0]][n[1]].value == my_chess[m[0]][m[1]].value:
                return 1
            #elif 1 == my_chess[m[0]][m[1]].value and 7 == my_chess[n[0]][n[1]].value and my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color:
            #    return 1
    if orgy+2 <= 3:
        n = a_map[orgy+2][orgx]
        if n == None:
            pass
        else:
            mc = my_chess[n[0]][n[1]]
            if 0 == mc.live or 1 == mc.back:
                pass
            elif 7 == my_chess[m[0]][m[1]].value and 1 == my_chess[n[0]][n[1]].value and my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color:
                pass
            elif my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color and my_chess[n[0]][n[1]].value == my_chess[m[0]][m[1]].value:
                return 1
            #elif 1 == my_chess[m[0]][m[1]].value and 7 == my_chess[n[0]][n[1]].value and my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color:
            #    return 1
    if orgx-2 >= 0:
        n = a_map[orgy][orgx-2]
        if n == None:
            pass
        else:
            mc = my_chess[n[0]][n[1]]
            if 0 == mc.live or 1 == mc.back:
                pass
            elif 7 == my_chess[m[0]][m[1]].value and 1 == my_chess[n[0]][n[1]].value and my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color:
                pass
            elif my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color and my_chess[n[0]][n[1]].value == my_chess[m[0]][m[1]].value:
                return 1
            #elif 1 == my_chess[m[0]][m[1]].value and 7 == my_chess[n[0]][n[1]].value and my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color:
            #    return 1
    if orgx+2 <= 7:
        n = a_map[orgy][orgx+2]
        if n == None:
            pass
        else:
            mc = my_chess[n[0]][n[1]]
            if 0 == mc.live or 1 == mc.back:
                pass
            elif 7 == my_chess[m[0]][m[1]].value and 1 == my_chess[n[0]][n[1]].value and my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color:
                pass
            elif my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color and my_chess[n[0]][n[1]].value == my_chess[m[0]][m[1]].value:
                return 1
            #elif 1 == my_chess[m[0]][m[1]].value and 7 == my_chess[n[0]][n[1]].value and my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color:
            #    return 1
    if orgy-1 >= 0 and orgx-1 >=0:
        n = a_map[orgy-1][orgx-1]
        if n == None:
            pass
        else:
            mc = my_chess[n[0]][n[1]]
            if 0 == mc.live or 1 == mc.back:
                pass
            elif 7 == my_chess[m[0]][m[1]].value and 1 == my_chess[n[0]][n[1]].value and my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color:
                pass
            elif my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color and my_chess[n[0]][n[1]].value == my_chess[m[0]][m[1]].value:
                return 1
            #elif 1 == my_chess[m[0]][m[1]].value and 7 == my_chess[n[0]][n[1]].value and my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color:
            #    return 1
    if orgy-1 >= 0 and orgx+1 <=7:
        n = a_map[orgy-1][orgx+1]
        if n == None:
            pass
        else:
            mc = my_chess[n[0]][n[1]]
            if 0 == mc.live or 1 == mc.back:
                pass
            elif 7 == my_chess[m[0]][m[1]].value and 1 == my_chess[n[0]][n[1]].value and my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color:
                pass
            elif my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color and my_chess[n[0]][n[1]].value == my_chess[m[0]][m[1]].value:
                return 1
            #elif 1 == my_chess[m[0]][m[1]].value and 7 == my_chess[n[0]][n[1]].value and my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color:
            #    return 1
    if orgy+1 <= 3 and orgx-1 >= 0:
        n = a_map[orgy+1][orgx-1]
        if n == None:
            pass
        else:
            mc = my_chess[n[0]][n[1]]
            if 0 == mc.live or 1 == mc.back:
                pass
            elif 7 == my_chess[m[0]][m[1]].value and 1 == my_chess[n[0]][n[1]].value and my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color:
                pass
            elif my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color and my_chess[n[0]][n[1]].value == my_chess[m[0]][m[1]].value:
                return 1
            #elif 1 == my_chess[m[0]][m[1]].value and 7 == my_chess[n[0]][n[1]].value and my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color:
            #    return 1
    if orgy+1 <= 3 and orgx+1 <= 7:
        n = a_map[orgy+1][orgx+1]
        if n == None:
            pass
        else:
            mc = my_chess[n[0]][n[1]]
            if 0 == mc.live or 1 == mc.back:
                pass
            elif 7 == my_chess[m[0]][m[1]].value and 1 == my_chess[n[0]][n[1]].value and my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color:
                pass
            elif my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color and my_chess[n[0]][n[1]].value == my_chess[m[0]][m[1]].value:
                return 1
            #elif 1 == my_chess[m[0]][m[1]].value and 7 == my_chess[n[0]][n[1]].value and my_chess[n[0]][n[1]].color != my_chess[m[0]][m[1]].color:
            #    return 1
    return 0

def scan_king(my_chess):
    global king_live
    
    for chr in my_chess:
        for ch in chr:
            if 7 == ch.value:
                king_live[ch.color] = ch.live

def save_step_and_break_long_capture(org, dest):
    global move_step
    global sindex
    global break_long_capture_dest
    global break_long_capture_org
    global com_ban_step
    
    if org != dest:
        move_step[sindex] = [com_color, org, dest]
        sindex = (sindex+1)%4
        br = 0
        while(br < len(break_long_capture_dest)):
            b = 0
            for d in break_long_capture_dest[br]:
                if dest == d:
                    del break_long_capture_dest[br]
                    del break_long_capture_org[br]
                    del com_ban_step[br]
                    b = 1
                    break
            if 0 == b:
                br += 1
                
        br = 0
        while(br < len(break_long_capture_org)):
            b = 0
            for o in break_long_capture_org[br]:
                if org == o:
                    del break_long_capture_dest[br]
                    del break_long_capture_org[br]
                    del com_ban_step[br]
                    b = 1
                    break
            if 0 == b:
                br += 1

def calc_cannon_mark(my_chess, a_map, owner_color):
    cannon_mark = [[0]*8, [0]*8, [0]*8, [0]*8]
    find_player_cannon_num = 0
    jump = 0
    
    if owner_color == player_color:
        return cannon_mark
    
    for r in range(0, 4):
        for c in range(0, 8):
            if 2 == find_player_cannon_num:
                break
            if 1 == my_chess[r][c].live and 0 == my_chess[r][c].back and player_color == my_chess[r][c].color and 2 == my_chess[r][c].value:
                find_player_cannon_num += 1
                (i, j) = (my_chess[r][c].row, my_chess[r][c].col)
                for ii in range(i-1, -1, -1):
                    if 1 == jump and a_map[ii][j] != None:
                        break
                    elif 1 == jump and None == a_map[ii][j]:
                        cannon_mark[ii][j] = 1
                    elif a_map[ii][j] != None:
                        jump = 1
                jump = 0
                for ii in range(i+1, 4, 1):
                    if 1 == jump and a_map[ii][j] != None:
                            break
                    elif 1 == jump and None == a_map[ii][j]:
                        cannon_mark[ii][j] = 1
                    elif a_map[ii][j] != None:
                        jump = 1
                jump = 0
                for jj in range(j-1, -1, -1):
                    if 1 == jump and a_map[i][jj] != None:
                        break
                    elif 1 == jump and None == a_map[i][jj]:
                        cannon_mark[i][jj] = 1
                    elif a_map[i][jj] != None:
                        jump = 1
                jump = 0
                for jj in range(j+1, 8, 1):
                    if 1 == jump and a_map[i][jj] != None:
                        break
                    elif 1 == jump and None == a_map[i][jj]:
                        cannon_mark[i][jj] = 1
                    elif a_map[i][jj] != None:
                        jump = 1
                  
    return cannon_mark

                
def move_score(org, dest, my_chess, a_map, owner_color):
    global max_value
    global mark
    #global max_cor
    global max_dist
    global com_will_eat_chess
    global will_eat_escape_chess
    global cannon_mark
    
    (orgy, orgx) = org
    (desty, destx) = dest
    
    if a_map[desty][destx] == None:
        #print 'org', org, 'dest', dest
        #print 'will dead dest', will_dead((desty, destx), main_chess, main_map, player_color), 'will dead org', will_dead((orgy, orgx), main_chess, main_map, player_color)
        if 1 == owner_next_can_eat_dead_p(org, dest, my_chess, a_map, owner_color):
            if 1 == opp_cannon_can_eat(org, dest, my_chess, a_map):
                return 7.5
            elif a_map[orgy][orgx] != None:
                m = a_map[orgy][orgx]
                if 3 == my_chess[m[0]][m[1]].value:
                    return 7
                else:
                    return 10
        elif 1 == will_eat2_more(org, dest, my_chess, a_map, owner_color):
            #print 'nem'
            return 8
        elif owner_color == player_color:
            #if 0 == will_dead((desty, destx), main_chess, main_map, com_color) and 1 == stand_will_dead_pity((orgy, orgx), main_chess, main_map, player_color):
            #    return 9
            #else:
            return 0
        elif 0 == dest_will_dead_owner_wont_eat(org, dest, main_chess, main_map, player_color) and 1 == stand_will_dead_pity((orgy, orgx), main_chess, main_map, com_color):
            #escape, 0 == will_dead((desty, destx), my_chess, com_color)
            #print 'will dead org', org, dest
            if 1 == next_cannon_can_eat_more(org, dest, a_map, my_chess):
                return -8
            else:
                return 9        
        
        if  2 == my_chess[a_map[orgy][orgx][0]][a_map[orgy][orgx][1]].value:
            af_map = copy.deepcopy(a_map)
            af_ch = copy.deepcopy(my_chess)
            if org != None and dest != None:
                af_map, af_ch = move(org, dest, af_map, af_ch)
                af_map, af_ch = all_chess_move(af_map, af_ch)
                cannon = af_ch[af_map[dest[0]][dest[1]][0]][af_map[dest[0]][dest[1]][1]]
                for pm in cannon.possible_move:
                    (pmy, pmx) = pm
                    am = af_map[pmy][pmx]
                    if None == am:
                        continue
                    c = af_ch[am[0]][am[1]]
                    if c.value > 5:
                        return 7.3            
            return 0
        
        max_value = 0
        max_dist = 32
        #max_cor = None
        mark = [[0]*8, [0]*8, [0]*8, [0]*8]
        org_value = my_chess[a_map[orgy][orgx][0]][a_map[orgy][orgx][1]].value
        if 1 == near2_have_same_value(org, my_chess, a_map, owner_color):
            #print 'nhsv'
            if 0 == will_dead_pity_even_equal(org, dest, my_chess, a_map, owner_color):
                return -0.1
        if 1 == caca(org, dest, my_chess, a_map, owner_color):
            #print 'caca'
            #following comment:No need due to function near2_have_same_value will check it
            #if 0 == caca(org, org, my_chess, a_map, owner_color):
            #    return org_value+0.001
            #else:
            #    return 0.1
            return org_value+0.001
            
        for ban in com_ban_step:
            if org == ban:
                return -0.1
        
        ncor = near(orgy, orgx)
        for nc in ncor:
            if a_map[nc[0]][nc[1]] != None:
                a = a_map[nc[0]][nc[1]]
                small_value = my_chess[a[0]][a[1]].value
                if player_color == my_chess[a[0]][a[1]].color and 1 == can_be_ate(small_value, org_value):
                    return -0.1
                
        cannon_mark = calc_cannon_mark(my_chess, a_map, owner_color)
        
        move_max_value(orgx, orgy, destx, desty, my_chess, a_map, org_value, my_chess[a_map[orgy][orgx][0]][a_map[orgy][orgx][1]].color, desty, destx)          
        
        #print 'max_value', max_value, 'max_cor', max_cor, 'org', org, 'dest', dest, 'owner_color', owner_color
        #print 'mark', mark
        
        #if 8 == max_value:
        #    return (float)(org_value)/100
        
        #print 'max_value = %g' % max_value
        #print 'mv', org, dest, max_dist
        
        if 9 == max_value:
            #print 'mv', org, dest, max_dist
            
            #if max_cor != None:
            #    if max_cor[0] != desty and max_cor[1] != destx:
            #        return 7.0 - 0.29*(abs(max_cor[0]-orgy)+abs(max_cor[1]-orgx))
            #    else:
            #        return 7.0 - 0.3*(abs(max_cor[0]-orgy)+abs(max_cor[1]-orgx))
            #else:
            #    return 7
            if max_dist != 0:
                if 7.0 > 0.25*max_dist:
                    return 7.0 - 0.25*max_dist
                else:
                    return 0.25 - (float)(max_dist)/100
            else:
                # impossible
                return 0
        else:
            #if max_value == 2:
            #    max_value = 5.5
            
            #if max_cor != None:
            #    if max_cor[0] != desty and max_cor[1] != destx:
            #        if max_value > 0.29*(abs(max_cor[0]-orgy)+abs(max_cor[1]-orgx)):
            #            return (float)(max_value) - 0.29*(abs(max_cor[0]-orgy)+abs(max_cor[1]-orgx))
            #        else:
            #            return 0.01
            #    elif max_value > 0.3*(abs(max_cor[0]-orgy)+abs(max_cor[1]-orgx)):
            #        return (float)(max_value) - 0.3*(abs(max_cor[0]-orgy)+abs(max_cor[1]-orgx))
            #    else:
            #        return 0.01
            if max_dist != 0:
                if max_value > 0.25 * max_dist:
                    return (float)(max_value) - 0.25 * max_dist
                else:
                    return 0.25 - (float)(max_dist)/100
            else:
                return -0.1
    
    elif 1 == my_chess[a_map[desty][destx][0]][a_map[desty][destx][1]].live:
        #print 'owner_color', owner_color, 'org', org, 'dest', dest, 'eating score', eating_value_to_score(my_chess[a_map[desty][destx][0]][a_map[desty][destx][1]].value, king_live, my_chess[a_map[orgy][orgx][0]][a_map[orgy][orgx][1]].color)
        #print 'owner_next_can_eat_dead_p %d' % owner_next_can_eat_dead_p(dest, dest, my_chess, a_map, 1-owner_color)
        if owner_color == com_color and 1 == owner_next_can_eat_dead_p(org, org, my_chess, a_map, owner_color) and 0 == stand_will_dead_pity((orgy, orgx), my_chess, a_map, com_color):
            if (orgy, orgx) in will_eat_escape_chess:
                return eating_value_to_score(my_chess[a_map[desty][destx][0]][a_map[desty][destx][1]].value, king_live, my_chess[a_map[orgy][orgx][0]][a_map[orgy][orgx][1]].color)
            else:
                if False == ((orgy, orgx) in com_will_eat_chess):
                    com_will_eat_chess.append((orgy, orgx))
                if my_chess[a_map[orgy][orgx][0]][a_map[orgy][orgx][1]].value != 2:
                    return 10 + float(eating_value_to_score(my_chess[a_map[desty][destx][0]][a_map[desty][destx][1]].value, king_live, my_chess[a_map[orgy][orgx][0]][a_map[orgy][orgx][1]].color))/5
                else:
                    return eating_value_to_score(my_chess[a_map[desty][destx][0]][a_map[desty][destx][1]].value, king_live, my_chess[a_map[orgy][orgx][0]][a_map[orgy][orgx][1]].color)
        else:
            if (orgy, orgx) in com_will_eat_chess:
                if my_chess[a_map[orgy][orgx][0]][a_map[orgy][orgx][1]].value != 2:
                    return 10 + float(eating_value_to_score(my_chess[a_map[desty][destx][0]][a_map[desty][destx][1]].value, king_live, my_chess[a_map[orgy][orgx][0]][a_map[orgy][orgx][1]].color))/5
                else:
                    return eating_value_to_score(my_chess[a_map[desty][destx][0]][a_map[desty][destx][1]].value, king_live, my_chess[a_map[orgy][orgx][0]][a_map[orgy][orgx][1]].color)
            else:
                if False == ((orgy, orgx) in will_eat_escape_chess):
                    will_eat_escape_chess.append((orgy, orgx))
                return eating_value_to_score(my_chess[a_map[desty][destx][0]][a_map[desty][destx][1]].value, king_live, my_chess[a_map[orgy][orgx][0]][a_map[orgy][orgx][1]].color)

def move_s(org, dest, a_map, a_ch):
    global cor
    global com_mv_map
    
    (orgi, orgj) = org
    (desti, destj) = dest
    
    if org == dest:
        print crash
    if None == a_map[desti][destj]:
        org_ch = a_ch[a_map[orgi][orgj][0]][a_map[orgi][orgj][1]]
        (org_ch.row, org_ch.col) = (desti, destj)
        #(org_ch.x, org_ch.y) = cor[org_ch.row][org_ch.col]
        com_mv_map = list(a_map[orgi][orgj])
        a_map[orgi][orgj] = None
        sound_move.play()
    else:
        #dest_ch = a_ch[a_map[desti][destj][0]][a_map[desti][destj][1]]
        org_ch  = a_ch[a_map[orgi][orgj][0]][a_map[orgi][orgj][1]]
        #dest_ch.live = 0
        (org_ch.row, org_ch.col) = (desti, destj)
        #(org_ch.x, org_ch.y) = cor[org_ch.row][org_ch.col]
        com_mv_map = list(a_map[orgi][orgj])
        a_map[orgi][orgj] = None
        sound_capture.play()
    
    return a_map, a_ch    
        
def move(org, dest, a_map, a_ch):
    global cor
    
    if org == dest:
        return a_map, a_ch
    
    (orgi, orgj) = org
    (desti, destj) = dest
    
    if None == a_map[desti][destj]:
        org_ch = a_ch[a_map[orgi][orgj][0]][a_map[orgi][orgj][1]]
        (org_ch.row, org_ch.col) = (desti, destj)
        (org_ch.x, org_ch.y) = cor[org_ch.row][org_ch.col]
        a_map[desti][destj] = (list(a_map[orgi][orgj])[0], list(a_map[orgi][orgj])[1])
        a_map[orgi][orgj] = None
    else:
        dest_ch = a_ch[a_map[desti][destj][0]][a_map[desti][destj][1]]
        org_ch  = a_ch[a_map[orgi][orgj][0]][a_map[orgi][orgj][1]]
        dest_ch.live = 0
        (org_ch.row, org_ch.col) = (desti, destj)
        (org_ch.x, org_ch.y) = cor[org_ch.row][org_ch.col]
        a_map[desti][destj] = (list(a_map[orgi][orgj])[0], list(a_map[orgi][orgj])[1])
        a_map[orgi][orgj] = None
    
    return a_map, a_ch    
    
def cant_move(a_map, a_ch, owner_color):
    a_map, a_ch = all_chess_move(a_map, a_ch)
    for chr in a_ch:
        for ch in chr:
            if ch.color == owner_color and 1 == ch.live:
                for pm in ch.possible_move:
                    return 0
    return 1

def temp_clac_num_back():
    cb = 0
    for chr in my_ch:
        for ch in chr:
            if ch.back == 1:
                cb += 1
    return cb
    
def com_think(a_map, a_ch):
    global open_score

    m = []
    
    min_score = 1000
    sc = 0
    
    a_map, a_ch = all_chess_move(a_map, a_ch)
    
    scan_king(a_ch)
    #print 'k_live', king_live
    
    if back_num > 0:
        open_score = 0
        m.append((None, None, 0))
        min_score = 0
        org = None
        dest = None
    else:
        open_score = None
    
    for chr in a_ch:
        for ch in chr:
            if ch.color == com_color and 1 == ch.live:
                for pm in ch.possible_move:
                    #print (ch.row, ch.col), pm, 'will dead pity', will_dead_pity((ch.row, ch.col), pm, a_ch, a_map, com_color)
                    if 0 == will_dead_pity((ch.row, ch.col), pm, a_ch, a_map, com_color):
                        score = sc - move_score((ch.row, ch.col), pm, a_ch, a_map, com_color)
                    else:
                        score = sc + 50 - move_score((ch.row, ch.col), pm, a_ch, a_map, com_color)
                    m.append(((ch.row, ch.col), pm, score))
                    #print 'm', m
                    if score < min_score:
                        min_score = score
                        org = (ch.row, ch.col)
                        dest = pm   
    
    #print 'map', a_map
    if len(m) > 1:
        mf = []
        for mm in m:
            m2 = []
            m3 = []
            #m4 = []
            #print 'mm', mm
            m2, a2_map, a2_ch= one_turn(a_map, a_ch, mm, player_color, mm[0], mm[1], mm[2], 0.9)
            if m2:
                max_index = m2.index(max(m2, key=lambda s:s[4]))
                #print 'm2 score', m2[max_index][4], m2[max_index][2], m2[max_index][3]
                if mm[0] == mm[1]:
                    open_score = m2[max_index][4]
                mf.append([mm[0], mm[1], m2[max_index][4]])
                #if m2[max_index][4] == mm[2] and back_num > 0:
                #    m2[max_index][2] = None
                #    m2[max_index][3] = None
                #if mm[0] == mm[1] or 1 == chess_num[player_color]:
                #    mf.append([mm[0], mm[1], m2[max_index][4]])
                #    continue
                #elif 0 == back_num and m2[max_index][4] == mm[2]:
                #    mf.append([mm[0], mm[1], m2[max_index][4]])
                #    continue                
                #m3, a3_map, a3_ch= one_turn(a2_map, a2_ch, mm, com_color, m2[max_index][2], m2[max_index][3], m2[max_index][4], 0.81)
                #if m3:
                #    mf2 = []
                #    for mm3 in m3:
                #        m4 = []
                #        m4, a4_map, a4_ch= one_turn(a3_map, a3_ch, mm, player_color, mm3[2], mm3[3], mm3[4], 0.729)
                #        if m4:
                #            max2_index = m4.index(max(m4, key=lambda s:s[4]))
                #            #print 'm4 score', m4[max2_index][4]
                #            mf2.append([mm[0], mm[1], m4[max2_index][4]])
                #    min_index = mf2.index(min(mf2, key=lambda s:s[2]))
                #    mf.append([mm[0], mm[1], mf2[min_index][2]])
                #else:
                #    mf.append([mm[0], mm[1], m2[max_index][4]])
        if mf:
            min_index = mf.index(min(mf, key=lambda s:s[2]))
            print 'mf', mf
            return mf[min_index][0], mf[min_index][1], mf[min_index][2]
        else:
            return org, dest, min_score
    elif 1 == len(m):
        return m[0][0], m[0][1], m[0][2]
    else:
        return None, None, 0     

def one_turn(a_map, a_ch, mm, owner_color, nexti, nextj, sc, div):
    m2 = []
    af_map = copy.deepcopy(a_map)
    af_ch = copy.deepcopy(a_ch)
    if nexti != None and nextj != None:
        af_map, af_ch = move(nexti, nextj, af_map, af_ch)
        af_map, af_ch = all_chess_move(af_map, af_ch)
    
    if owner_color == player_color and 1 == cant_move(af_map, af_ch, player_color):
        m2.append([mm[0], mm[1], None, None, sc])
        return m2, af_map, af_ch

    if back_num > 0:
        m2.append([mm[0], mm[1], None, None, sc])
    
    for chr in af_ch:
        for ch in chr:
            if ch.color == owner_color and 1 == ch.live and ch.back < 1:
                for pm in ch.possible_move:
                    if 0 == will_dead_pity((ch.row, ch.col), pm, af_ch, af_map, owner_color):
                        #print (ch.row, ch.col), pm, 'owner_color', owner_color, 'ni', nexti, 'nj', nextj
                        if owner_color == player_color:
                            if 0 == will_dead_pity_even_equal((ch.row, ch.col), pm, af_ch, af_map, owner_color):#equal
                                score = sc + div * move_score((ch.row, ch.col), pm, af_ch, af_map, player_color)
                                #print 'score', score
                            else:
                                #print 'sc', sc
                                score = sc
                        else:
                            score = sc - div * move_score((ch.row, ch.col), pm, af_ch, af_map, com_color)
                    else:
                        #print (ch.row, ch.col), pm, 'owner_color', owner_color, 'ni', nexti, 'nj', nextj
                        if owner_color == com_color:
                            score = sc + 40 - div * move_score((ch.row, ch.col), pm, af_ch, af_map, com_color)
                            #print 'sc40', score
                        else:
                            score = sc - 8
                            #print 'sc10', score, (ch.row, ch.col), pm
                    
                    m2.append([mm[0], mm[1], (ch.row, ch.col), pm, score])
                    
    return m2, af_map, af_ch

def dest_will_dead_owner_wont_eat(org, dest, a_ch, a_map, opp_color):
    n = a_map[org[0]][org[1]]
    m = a_map[dest[0]][dest[1]]
    if None == n:
        return 0
    elif m != None:
    #eat
        return 0
    
    af_map = copy.deepcopy(a_map)
    af_ch = copy.deepcopy(a_ch)
    af_map, af_ch = move(org, dest, af_map, af_ch)
    af_map, af_ch = all_chess_move(af_map, af_ch)
    mm = af_map[dest[0]][dest[1]]
    my = af_ch[mm[0]][mm[1]]
    
    for chr in af_ch:
        for ch in chr:
            if ch == my:
                continue
            if 1 == ch.live and ch.back < 1 and ch.color == opp_color: 
                for pm in ch.possible_move:
                    if pm == dest:
                        return 1
    return 0
    
def will_dead(org, a_ch, a_map, opp_color):
    n = a_map[org[0]][org[1]]
    if None == n:
        return 0
    my = a_ch[n[0]][n[1]]
    for chr in a_ch:
        for ch in chr:
            if ch == my:
                continue
            if 1 == ch.live and ch.back < 1 and ch.color == opp_color: 
                for pm in ch.possible_move:
                    if pm == org:
                        return 1
    return 0

def will_eat2_more(nexti, nextj, a_ch, a_map, owner_color):    
    opp_color = 1-owner_color
    can_eat = 0
    af_map = copy.deepcopy(a_map)
    af_ch = copy.deepcopy(a_ch)
    if nexti != None and nextj != None:
        af_map, af_ch = move(nexti, nextj, af_map, af_ch)
        af_map, af_ch = all_chess_move(af_map, af_ch)
    for chr in af_ch:
        for ch in chr:
            if 1 == ch.live and ch.back < 1 and ch.color == owner_color:
                for pm in ch.possible_move:
                    n = af_map[pm[0]][pm[1]]
                    if n != None:
                        nch = af_ch[n[0]][n[1]]
                        #print 'ch_value', ch.value, nch.value
                        if ch.value == nch.value:
                            continue
                    if 1 == stand_will_dead_pity(pm, af_ch, af_map, opp_color):
                        can_eat += 1
    if can_eat >= 2:
        return 1
    else:
        return 0

def owner_next_can_eat_dead_p(nexti, nextj, a_ch, a_map, owner_color):
    opp_color = 1-owner_color
    af_map = copy.deepcopy(a_map)
    af_ch = copy.deepcopy(a_ch)
    if nexti != None and nextj != None:
        af_map, af_ch = move(nexti, nextj, af_map, af_ch)
        af_map, af_ch = all_chess_move(af_map, af_ch)
    m = af_map[nextj[0]][nextj[1]]
    my = af_ch[m[0]][m[1]]
    #print 'nexti', nexti, 'nextj', nextj
    for eat_pm in my.possible_move:
        if af_map[eat_pm[0]][eat_pm[1]] != None:
            eat_step = 0
            n = af_map[eat_pm[0]][eat_pm[1]]
            #print 'eat_pm', eat_pm
            nch = af_ch[n[0]][n[1]]
            #print 'value', nch.value, my.value
            if nch.value == my.value:
                continue
            if 1 == nch.live and nch.back < 1 and nch.color == opp_color:
                if 1 == stand_will_dead_pity(eat_pm, af_ch, af_map, opp_color):
                    for pm in nch.possible_move:
                        if 1 == will_dead_pity_uncheck_will_dead(eat_pm, pm, af_ch, af_map, opp_color):
                            eat_step += 1
                        #print 'eat_step', eat_step, 'pm', pm, 'len', len(nch.possible_move)
                    if eat_step == len(nch.possible_move):
                        return 1
    return 0
    
def stand_will_dead_pity(org, a_ch, a_map, owner_color):
    opp_color = 1-owner_color
    n = a_map[org[0]][org[1]]
    if None == n:
        return 0
    my = a_ch[n[0]][n[1]]
    for chr in a_ch:
        for ch in chr:
            if ch == my:
                continue
            if 1 == ch.live and ch.back < 1 and ch.color == opp_color: 
                for pm in ch.possible_move:
                    if pm == org:
                        if 0 == will_dead_pity((ch.row, ch.col) ,pm, a_ch, a_map, opp_color):
                            return 1
    return 0

def will_dead_pity_uncheck_will_dead(nexti, nextj, a_ch, a_map, owner_color):
    global king_live
    
    (y, x) = nexti
    a = a_map[y][x]

    if nextj != None:
        (ii, jj) = nextj
        b = a_map[ii][jj]
        if b != None:
            if 2 == a_ch[a[0]][a[1]].value:
                if a_ch[b[0]][b[1]].value > 4:
                    return 0
            if a_ch[b[0]][b[1]].value == a_ch[a[0]][a[1]].value:
                return 0
    
    af_map = copy.deepcopy(a_map)
    af_ch = copy.deepcopy(a_ch)
    af_map, af_ch = move(nexti, nextj, af_map, af_ch)
    af_map, af_ch = all_chess_move(af_map, af_ch)
    opp_color = 1 - owner_color

    pity = 0
    i2 = None
    j2 = None
    
    #print 'b', b
    #print 'ea', eating_value_to_score(a_ch[a[0]][a[1]].value, king_live, 1-owner_color)
    
    for chr in af_ch:
        if 1 == pity:
            break
        for ch in chr:
            if ch.color == opp_color and 1 == ch.live:
                for pm in ch.possible_move:
                    if pm == nextj:
                        if b == None:
                            i2 = (ch.row, ch.col)
                            j2 = pm
                            pity = 1
                            break
                        elif eating_value_to_score(a_ch[a[0]][a[1]].value, king_live, 1-owner_color) > eating_value_to_score(a_ch[b[0]][b[1]].value, king_live, owner_color):
                            i2 = (ch.row, ch.col)
                            j2 = pm
                            pity = 1
                            break
    
    #if 1 == pity:
    #    print 'pity', nexti, nextj
    #    print 'i2', i2, 'j2', j2
    
    if i2!= None and j2!= None:                    
        af2_map = copy.deepcopy(af_map)
        af2_ch = copy.deepcopy(af_ch)
        af2_map, af2_ch = move(i2, j2, af2_map, af2_ch)
        af2_map, af2_ch = all_chess_move(af2_map, af2_ch)
        
        (ii, jj) = j2
        b = af2_map[ii][jj]
        
        #print 'e a_ch[a]', eating_value_to_score(a_ch[a[0]][a[1]].value, king_live, 1-owner_color)
        #print 'e af2_ch[b]', eating_value_to_score(af2_ch[b[0]][b[1]].value, king_live, owner_color)
        
        for chr in af2_ch:
            if 0 == pity:
                break
            for ch in chr:
                if ch.color == owner_color and 1 == ch.live:
                    for pm in ch.possible_move:
                        if pm == j2 and eating_value_to_score(a_ch[a[0]][a[1]].value, king_live, 1-owner_color) <= eating_value_to_score(af2_ch[b[0]][b[1]].value, king_live, owner_color):
                            pity = 0
                            break    
    return pity

def will_dead_pity_even_equal(nexti, nextj, a_ch, a_map, owner_color):
    global king_live
    
    #if 1 == will_dead(nexti, a_ch, a_map, 1-owner_color):
    #    return 0
    
    (y, x) = nexti
    a = a_map[y][x]

    if nextj != None:
        (ii, jj) = nextj
        b = a_map[ii][jj]
        if b != None:
            if 2 == a_ch[a[0]][a[1]].value:
                if a_ch[b[0]][b[1]].value > 4:
                    return 0
            #if a_ch[b[0]][b[1]].value == a_ch[a[0]][a[1]].value:
            #    return 0
    
    af_map = copy.deepcopy(a_map)
    af_ch = copy.deepcopy(a_ch)
    af_map, af_ch = move(nexti, nextj, af_map, af_ch)
    af_map, af_ch = all_chess_move(af_map, af_ch)
    opp_color = 1 - owner_color

    pity = 0
    i2 = None
    j2 = None
    
    #print 'b', b
    #print 'ea', eating_value_to_score(a_ch[a[0]][a[1]].value, king_live, 1-owner_color)
    
    for chr in af_ch:
        if 1 == pity:
            break
        for ch in chr:
            if ch.color == opp_color and 1 == ch.live:
                for pm in ch.possible_move:
                    if pm == nextj:
                        if b == None:
                            i2 = (ch.row, ch.col)
                            j2 = pm
                            pity = 1
                            break
                        elif eating_value_to_score(a_ch[a[0]][a[1]].value, king_live, 1-owner_color) >= eating_value_to_score(a_ch[b[0]][b[1]].value, king_live, owner_color):
                            i2 = (ch.row, ch.col)
                            j2 = pm
                            pity = 1
                            break
    
    #if 1 == pity:
    #    print 'pity', nexti, nextj
    #    print 'i2', i2, 'j2', j2
    
    if i2!= None and j2!= None:                    
        af2_map = copy.deepcopy(af_map)
        af2_ch = copy.deepcopy(af_ch)
        af2_map, af2_ch = move(i2, j2, af2_map, af2_ch)
        af2_map, af2_ch = all_chess_move(af2_map, af2_ch)
        
        (ii, jj) = j2
        b = af2_map[ii][jj]
        
        #print 'e a_ch[a]', eating_value_to_score(a_ch[a[0]][a[1]].value, king_live, 1-owner_color)
        #print 'e af2_ch[b]', eating_value_to_score(af2_ch[b[0]][b[1]].value, king_live, owner_color)
        
        for chr in af2_ch:
            if 0 == pity:
                break
            for ch in chr:
                if ch.color == owner_color and 1 == ch.live:
                    for pm in ch.possible_move:
                        if pm == j2 and eating_value_to_score(a_ch[a[0]][a[1]].value, king_live, 1-owner_color) < eating_value_to_score(af2_ch[b[0]][b[1]].value, king_live, owner_color):
                            pity = 0
                            break    
    return pity
    
def will_dead_pity(nexti, nextj, a_ch, a_map, owner_color):
    global king_live
    
    if 1 == will_dead(nexti, a_ch, a_map, 1-owner_color):
        return 0
    
    (y, x) = nexti
    a = a_map[y][x]
    
    if nextj != None:
        (ii, jj) = nextj
        b = a_map[ii][jj]
        if b != None:
            if 2 == a_ch[a[0]][a[1]].value:
                if a_ch[b[0]][b[1]].value > 5:
                    return 0
            if a_ch[b[0]][b[1]].value == a_ch[a[0]][a[1]].value:
                return 0
    
    af_map = copy.deepcopy(a_map)
    af_ch = copy.deepcopy(a_ch)
    af_map, af_ch = move(nexti, nextj, af_map, af_ch)
    af_map, af_ch = all_chess_move(af_map, af_ch)
    opp_color = 1 - owner_color

    pity = 0
    i2 = None
    j2 = None
    i3 = None
    j3 = None
    
    #print 'b', b
    #print 'ea', eating_value_to_score(a_ch[a[0]][a[1]].value, king_live, 1-owner_color)
    
    for chr in af_ch:
        if 1 == pity:
            break
        for ch in chr:
            if ch.color == opp_color and 1 == ch.live:
                for pm in ch.possible_move:
                    if pm == nextj:
                        if b == None:
                            i2 = (ch.row, ch.col)
                            j2 = pm
                            pity = 1 
                            break
                        elif eating_value_to_score(a_ch[a[0]][a[1]].value, king_live, 1-owner_color) > eating_value_to_score(a_ch[b[0]][b[1]].value, king_live, owner_color):
                            i2 = (ch.row, ch.col)
                            j2 = pm
                            pity = 1
                            break
    
    #if 1 == pity:
    #    print 'pity', nexti, nextj
    #    print 'i2', i2, 'j2', j2
    
    if i2!= None and j2!= None:                    
        af2_map = copy.deepcopy(af_map)
        af2_ch = copy.deepcopy(af_ch)
        af2_map, af2_ch = move(i2, j2, af2_map, af2_ch)
        af2_map, af2_ch = all_chess_move(af2_map, af2_ch)
        
        (ii, jj) = j2
        b = af2_map[ii][jj]
        
        #print 'e a_ch[a]', eating_value_to_score(a_ch[a[0]][a[1]].value, king_live, 1-owner_color)
        #print 'e af2_ch[b]', eating_value_to_score(af2_ch[b[0]][b[1]].value, king_live, owner_color)
        #print 'i2', i2, 'j2', j2
        #print 'king_live', king_live
        
        for chr in af2_ch:
            if 0 == pity:
                break
            for ch in chr:
                if ch.color == owner_color and 1 == ch.live:
                    for pm in ch.possible_move:
                        if pm == j2 and eating_value_to_score(a_ch[a[0]][a[1]].value, king_live, 1-owner_color) <= eating_value_to_score(af2_ch[b[0]][b[1]].value, king_live, owner_color):
                            i3 = (ch.row, ch.col)
                            j3 = pm
                            pity = 0
                            break 
    
    #print 'pity', pity
    if i3!= None and j3!= None:                    
        af3_map = copy.deepcopy(af2_map)
        af3_ch = copy.deepcopy(af2_ch)
        af3_map, af3_ch = move(i3, j3, af3_map, af3_ch)
        af3_map, af3_ch = all_chess_move(af3_map, af3_ch)
        
        #(ii, jj) = j3
        #b = af3_map[ii][jj]
        
        for chr in af3_ch:
            if 1 == pity:
                break
            for ch in chr:
                if ch.color == opp_color and 1 == ch.live:
                    for pm in ch.possible_move:
                        if pm == j3:
                            pity = 1
                            break     
    return pity
        
def eating_value_to_score(value, king, owner_color):
    if 1 == value:
        if 1 == king[owner_color]:
            return 24
        else:
            return 20
    elif 2 == value:
        return 150
    elif 3 == value:
        return 23
    elif 4 == value:
        return 49
    elif 5 == value:
        return 99
    elif 6 == value:
        return 300
    elif 7 == value:
        return 599

def display_font():
    
    if 1 == player_win:
        winer = u"玩家1勝!!!"
        screen.blit(write(winer, (0, 0, 255)), (text_x, text_y))
    elif -1 == player_win:
        winer = u"玩家2勝!!!"
        screen.blit(write(winer, (0, 255, 0)), (text_x, text_y))
    elif 1 == first:
        if 1 == player1_first:
            up = u"玩家1先"
            screen.blit(write(up, (150, 150, 150)), (text_x, text_y))
        else:
            uc = u"玩家2先"
            screen.blit(write(uc, (150, 150, 150)), (text_x, text_y))
    elif turn_id == player_color:
        up = u"玩家1下"
        if 1 == player_color:
            screen.blit(write(up, (255, 0, 0)), (text_x, text_y))
        else:
            screen.blit(write(up, (0, 0, 0)), (text_x, text_y))
    else: #turn_id == com_color or turn_id == 2
        uc = u"玩家2下"
        if 1 == player2_color:
            screen.blit(write(uc, (255, 0, 0)), (text_x, text_y))
        else:
            screen.blit(write(uc, (0, 0, 0)), (text_x, text_y))       
        
def write(msg="pygame is cool", color= (0,0,0)):    
    #myfont = pygame.font.SysFont("None", 32) #To avoid py2exe error
    myfont = pygame.font.Font("wqy-zenhei.ttf",14)
    mytext = myfont.render(msg, True, color)
    mytext = mytext.convert_alpha()
    return mytext 

def clean_back_n1_to_0(a_ch):
    for chr in a_ch:
        for ch in chr:
            if -1 == ch.back:
                ch.back = 0
    return a_ch
    
# =============================================================================================================

def client( host, port ):
    global cstart_x
    global cstart_y
    global cstart_x2
    global cstart_y2
    global chess_index
    global turn_id
    global player_color
    global player2_color
    global host_color
    global com_color
    global player1_first
    global main_chess
    global main_map
    global cor        # 紀錄所有棋盤格子上的圖像座標
    global first
    global player_win
    global chess_num
    global com_moving_end
    global back_num
    global king_live
    global move_step
    global sindex
    global break_long_capture_dest
    global break_long_capture_org
    global com_ban_step

    sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    sock.connect( ( host, port ) )
    print( 'Client has been assigned socket name',sock.getsockname() )

    
    selected_c = None
    player_win = 0
    player_color = 0
    player2_color = 1
    com_color = 1
    first = 1
    moving = 1
    com_mv = 0
    com_moving_end = 1
    game_start = 1
    chess_num = [16, 16]
    back_num = 32
    break_long_capture_dest = []
    break_long_capture_org = []
    com_ban_step = []
    move_step = [None, None, None, None]
    sindex = 0

    recv_data = sock.recv( 1 )
    player1_first = int( recv_data[0:1], 10 )
    turn_id = 1 - player1_first     # 玩家一暫定color為0,玩家二暫定color為1,之後再根據抽到的第一個顏色來重新決定雙方顏色
    
    recv_data = sock.recv( MAX_BYTES )
    chess_index = pickle.loads( recv_data ) # 讀取接收到的棋盤資訊

    for i in range(0, 4):
        for j in range(0, 4):
            ch = chess(chess_index[8*i+j], (i, j), chess_back.get_size())
            main_chess[i][j] = ch
            cor[i][j] = (ch.x, ch.y)
            main_map[i][j] = (i, j)
    for i in range(0, 4):
        for j in range(0, 4):
            ch = chess(chess_index[8*i+4+j], (i, 4+j), chess_back.get_size())
            main_chess[i][4+j] = ch
            cor[i][4+j] = (ch.x, ch.y)
            main_map[i][4+j] = (i, 4+j)
   
    # 將棋盤和棋子全部印到視窗上
    screen.blit(background, (0,0))
    screen.blit(new_game, (new_game_iconi, new_game_iconj))
    display_font()

    for cr in main_chess:
        for c in cr:
            c.draw(screen)

    pygame.display.update()
    # Test data
    #first = 0
    #com_color = 1
    #player_color = 0
    #turn_id = 1
    #back_num = 16
    ## chess_num[0] = 3
    ## chess_num[1] = 3
    #
    ##for i in range(0, 4):
    #for j in range(0, 8):
    #    main_chess[1][j].live = 0
    #    main_map[1][j] = None
    #
    #for i in range(0, 4):
    #    main_chess[i][5].live = 0
    #    main_map[i][5] = None
    #
    #ch = chess(5, (3, 2), chess_back.get_size())
    #ch.back = 0
    #ch.live = 1
    #main_chess[3][2] = ch
    #main_map[3][2] = (3, 2)
    #
    #ch = chess(0, (2, 2), chess_back.get_size())
    #ch.back = 0
    #ch.live = 1
    #main_chess[2][2] = ch
    #main_map[2][2] = (2, 2)
    #
    #ch = chess(1, (3, 3), chess_back.get_size())
    #ch.back = 0
    #ch.live = 1
    #main_chess[3][3] = ch
    #main_map[3][3] = (3, 3)
    #
    #ch = chess(2, (3, 1), chess_back.get_size())
    #ch.back = 0
    #ch.live = 1
    #main_chess[3][1] = ch
    #main_map[3][1] = (3, 1)
    #
    #ch = chess(30, (1, 5), chess_back.get_size())
    #ch.back = 0
    #ch.live = 1
    #main_chess[1][5] = ch
    #main_map[1][5] = (1, 5)
    #        
    #ch = chess(7, (3, 6), chess_back.get_size())
    #ch.back = 0
    #ch.live = 1
    #main_chess[3][6] = ch
    #main_map[3][6] = (3, 6)
    #
    #ch = chess(12, (1, 0), chess_back.get_size())
    #ch.back = 0
    #ch.live = 1
    #main_chess[1][0] = ch
    #main_map[1][0] = (1, 0)
    #End Test data

    while 0 == player_win:
        if 1 == game_start: # 開始一個新遊戲時要播放的特殊音效
            sound_new.play()
            game_start = 0 # 播放玩之後則不再標注為新遊戲


        no_move = 1
        if 2 == turn_id: # 處理移動棋子的階段(?)
            for cr in main_chess:
                for c in cr:
                    com_mv = 0
                    if c.x != cor[c.row][c.col][0]:   # x軸 當偵測到該棋子的圖像沒有在他本來該在的座標上,則開始逐步調整x的位置,以累加的方式讓過程以動畫呈現
                        c.x = c.x+1 if c.x < cor[c.row][c.col][0] else c.x-1 # 棋子圖片往x軸方向移動,+1或是-1
                        com_mv = 1
                        if (c.x, c.y) == cor[c.row][c.col]: # 棋子圖片已經到達指定位置
                            if main_map[c.row][c.col] != None: # 當指定位置原本已經有其他棋子在時,代表吃子的動作
                                (desti, destj) = main_map[c.row][c.col] # 記下該點的map位置
                                dest_ch = main_chess[desti][destj]      # 取得該map位置的棋子
                                dest_ch.live = 0                        # 將該旗子標示為未存活,代表已經被吃掉
                                chess_num[dest_ch.color] -= 1           # 該色棋子數量減一
                            main_map[c.row][c.col] = (com_mv_map[0], com_mv_map[1])
                            turn_id = host_color
                    if c.y != cor[c.row][c.col][1]:   # y軸 原理同上
                        c.y = c.y+1 if c.y < cor[c.row][c.col][1] else c.y-1
                        com_mv = 1  
                        if (c.x, c.y) == cor[c.row][c.col]:
                            if main_map[c.row][c.col] != None:
                                (desti, destj) = main_map[c.row][c.col]
                                dest_ch = main_chess[desti][destj]
                                dest_ch.live = 0
                                chess_num[dest_ch.color] -= 1
                            main_map[c.row][c.col] = (com_mv_map[0], com_mv_map[1])
                            turn_id = host_color
                    if 1 == com_mv: 
                        no_move = 0
                        c.draw(screen)
                        com_mv = 0
            if 1 == no_move:    # 動畫播放結束
                turn_id = host_color

        if selected_c != None:
            selected_c.move()
            selected_c.draw(screen)
      
        # chess_ai() 將ai的部份拿掉

        # 玩家一行動時的狀態


        if turn_id == player_color:             # player1移動時的狀態,player1為server端,所以等待server端的傳來的資料
            if 0 == back_num and 1 == cant_move(main_map, main_chess, player2_color):
                print 'player1 cant move'
                player_win = 1

            if first == 1:  # 如果是第一回合,代表server端必須要告知他第一個抽中的顏色
                recv_data = sock.recv( 1 )
                pygame.event.clear() # 為了確保沒有多餘的動作,每次接收資料之後先清除event
                if recv_data == '1':
                    player_color = 1
                elif recv_data == '0':
                    player_color = 0

                player2_color = 1 - player_color # player1的顏色會和player2相反
                host_color = player2_color        # 紀錄本機端的顏色
                first = 0

            recv_data = sock.recv( MAX_BYTES)  # 從client端傳來的動作資料,此種資料有三種可能,翻開某個座標的棋,移動某個旗子到另一個棋子,投降
            pygame.event.clear() # # 為了確保沒有多餘的動作,每次接收資料之後先清除event

            if recv_data[0:4] == 'surr' or recv_data[0:4] == 'urr':   # 傳來投降的字串,client player1放棄比賽
                player_win = -1
            elif recv_data[0:4] == 'open':  # client翻開一顆覆蓋的棋子
                # 取得那個棋子的map位置
                map_i = int( recv_data[4:5], 10 ) 
                map_j = int( recv_data[5:6], 10 )
                main_chess[map_i][map_j].back = -1
                back_num -= 1
                turn_id = player2_color
            elif recv_data[0:4] == 'move':   # 將棋子進行移動
                # 首先紀錄下要移動旗子的座標
                org = ( int( recv_data[4:5] ), int( recv_data[5:6] ) )
                dest = ( int( recv_data[6:7] ), int( recv_data[7:8] ) )
                main_map, main_chess = move_s( org, dest, main_map, main_chess )
                
                turn_id = 2                                                          # 移完棋子之後進入播放動畫的階段
            # XXXXXXXXX

        # 到此為只是player1行動的狀態

        # 接著是player2的狀態,必須將處理的玩家動作送到player1去

        if turn_id == player2_color:
            if 0 == back_num and 1 == cant_move(main_map, main_chess, player2_color):
                print 'player2 cant move'
                player_win = 1

            for event in pygame.event.get():
                if event.type == QUIT:
                    exit()
                elif event.type == pygame.MOUSEBUTTONDOWN and turn_id == player2_color:     # 按下滑鼠的狀況
                    (mouseX, mouseY) = pygame.mouse.get_pos()
                    if new_game_iconi < mouseX < new_game_iconi + new_game.get_width() and new_game_iconj < mouseY < new_game_iconj + new_game.get_height(): # 按下投降記號,印出遊戲結果並開啟新遊戲
                        send_data = 'surr'
                        sock.sendall( send_data )
                        player_win = 1
                    main_map, main_chess = all_chess_move(main_map, main_chess) # 查出所有棋子可行的行動(不確定?)
                    sound_click.play()
                    click_once = 0             # 紀錄是否已經按了某個棋子的變數
                    for chr in main_chess:
                        for chc in chr:
                            if 0 == click_once: # 如果尚未按住某個棋子,則會根據點選位置的座標來判斷他是否會按到某個棋
                                ch_index = chc.click((mouseX, mouseY))
                                if ch_index != None: # 如果該座標可以找到棋子,代表玩家點選了一個棋子
                                    if 0 == player1_first and 1 == first:                            # 第一回合的情境,這個時候會判斷玩家弟一個選擇的棋子顏色,並將該顏色設定為玩家顏色
                                        turn_id = index_to_color(ch_index)                          # 之後變會將另一玩家顏色設定為相對的另一色
                                        player2_color = turn_id
                                        sock.sendall( str( player2_color ) )                           # 此外還要告知另一個玩家自己抽到的顏色
                                        host_color = player2_color
                                        ( click_i, click_j ) = main_map[chc.row][chc.col]

                                        com_color = 1 - player2_color
                                        player_color = 1 - player2_color
                                        first = 0                                                   # 取消第一回合的flag
                                        selected_c = None                                           # 由於第一回合所有旗子都必定是覆蓋的
                                        back_num -= 1
                                        send_data = 'open{}{}'.format( click_i, click_j )
                                        sock.sendall( send_data )
                                        turn_id = player_color
                                    elif -1 == ch_index and chc.color == player2_color:              # 棋子並非覆蓋,況且現在輪到player2,當棋子為非覆蓋的時候click會回傳-1
                                        selected_c = chc
                                    elif ch_index != -1 and 0 == first:                             # 棋子處於覆蓋的狀況,並且已經不是第一回合了
                                        ( click_i, click_j ) = main_map[chc.row][chc.col]
                                        selected_c = None
                                        back_num -= 1
                                        send_data = 'open{}{}'.format( click_i, click_j )
                                        sock.sendall( send_data )
                                        turn_id = player_color
                                    click_once = 1
                                    break
                elif event.type == pygame.MOUSEBUTTONUP and turn_id == player2_color:                # 回合輪到player1時放開滑鼠時的動作
                    if selected_c != None:
                        (mouseX, mouseY) = pygame.mouse.get_pos()
                        moving = 0
                        for pm in selected_c.possible_move:
                            if pm == mouse_position_to_block(mouseX, mouseY, chess_back):           # mouse_position_to_block將滑鼠位置轉換為棋盤位置的function
                                if main_map[pm[0]][pm[1]] != None:                                  # 當移動的目標不是空的位置時,代表要進行吃子的動作
                                    main_chess[main_map[pm[0]][pm[1]][0]][main_map[pm[0]][pm[1]][1]].live = 0
                                    chess_num[main_chess[main_map[pm[0]][pm[1]][0]][main_map[pm[0]][pm[1]][1]].color] -= 1
                                    sound_capture.play()
                                else:
                                    sound_move.play()
                                main_map[pm[0]][pm[1]] = main_map[selected_c.row][selected_c.col]   # 目標位置的棋子變為來源位置原本的旗子
                                main_map[selected_c.row][selected_c.col] = None                     # 來源位置的棋已經走了,標記為none
                                org = (selected_c.row, selected_c.col)
                                selected_c.x = cor[pm[0]][pm[1]][0]
                                selected_c.y = cor[pm[0]][pm[1]][1]
                                selected_c.row = pm[0]
                                selected_c.col = pm[1]
                                dest = (selected_c.row, selected_c.col)

                                send_data = 'move{}{}{}{}'.format( org[0], org[1], dest[0], dest[1] ) # 送出移動的座標!!!!!!!!!!!!!!!!!!!!!!
                                sock.sendall( send_data )

                                moving = 1
                                turn_id = player_color
                                move_step[sindex] = [selected_c.color, org, dest]
                                #print move_step[sindex]
                                sindex = (sindex+1)%4

                                br = 0
                                while(br < len(break_long_capture_dest)):
                                    b = 0
                                    for d in break_long_capture_dest[br]:
                                        if dest == d:
                                            del break_long_capture_dest[br]
                                            del break_long_capture_org[br]
                                            del com_ban_step[br]
                                            b = 1
                                            break
                                    if 0 == b:
                                        br += 1
                                br = 0
                                while(br < len(break_long_capture_org)):
                                    b = 0
                                    for o in break_long_capture_org[br]:
                                        if org == o:
                                            del break_long_capture_dest[br]
                                            del break_long_capture_org[br]
                                            del com_ban_step[br]
                                            b = 1
                                            break
                                    if 0 == b:
                                        br += 1

                                break

                        if 0 == moving:
                           (selected_c.x, selected_c.y) = cor[selected_c.row][selected_c.col] 

                        selected_c.speed = 0
                        selected_c = None
                        moving = 1
                        break
                    else:
                        moving = 1
        
        if 1 == moving:
            main_map, main_chess = all_chess_move(main_map, main_chess)
            moving = 0
            
        if selected_c != None:                      # 此為按住棋子拖曳時的動畫呈現
            (mouseX, mouseY) = pygame.mouse.get_pos()
            dx = mouseX - selected_c.x
            dy = mouseY - selected_c.y
            dx -= selected_c.size[0]/2
            dy -= selected_c.size[1]/2
            selected_c.angle = 0.5*math.pi + math.atan2(dy, dx)
            selected_c.speed = math.hypot(dx, dy) * 0.1

        if 0 == chess_num[player_color]:
            player_win = -1

        elif 0 == chess_num[player2_color]:
            player_win = 1
            
        if 1 == player_win:
            screen.blit(background, (0,0))
            display_font()
            for cr in main_chess:
                for c in cr:
                    c.draw(screen)
            sound_win.play()
            pygame.display.update()
            time.sleep(5)
        elif -1 == player_win:
            screen.blit(background, (0,0))
            display_font()
            for cr in main_chess:
                for c in cr:
                    c.draw(screen)
            sound_loss.play()
            pygame.display.update()
            time.sleep(5)
            
        # 將棋盤,訊息,投降符號,棋子全部畫到螢幕上
        screen.blit(background, (0,0))
        screen.blit(new_game, (new_game_iconi, new_game_iconj))

        display_font()
        for cr in main_chess:
            for c in cr:
                c.draw(screen)
        pygame.display.update()
            
    exit()
    # end of client()

# =============================================================================================================

def server( interface, port ):
    global cstart_x
    global cstart_y
    global cstart_x2
    global cstart_y2
    global chess_index
    global turn_id
    global player_color
    global player2_color
    global host_color
    global com_color
    global player1_first
    global main_chess
    global main_map
    global cor        # 紀錄所有棋盤格子上的圖像座標
    global first
    global player_win
    global chess_num
    global com_moving_end
    global back_num
    global king_live
    global move_step
    global sindex
    global break_long_capture_dest
    global break_long_capture_org
    global com_ban_step

    sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    sock.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
    sock.bind( ( interface, port ) )
    sock.listen( 1 )
    print( 'Socket listening at', sock.getsockname() )
    sc, sockname = sock.accept()     # 成功和client建立連線
    
    selected_c = None
    player_win = 0
    player_color = 0
    player2_color = 1
    com_color = 1
    first = 1
    moving = 1
    com_mv = 0
    com_moving_end = 1
    game_start = 1
    chess_num = [16, 16]
    back_num = 32
    break_long_capture_dest = []
    break_long_capture_org = []
    com_ban_step = []
    move_step = [None, None, None, None]
    sindex = 0

    player1_first = random.randint(0, 1)
    send_data = str( player1_first )
    sc.sendall( send_data )
    turn_id = 1 - player1_first     # 玩家一暫定color為0,玩家二暫定color為1,之後再根據抽到的第一個顏色來重新決定雙方顏色
    
    chess_index = ini_random_chess(chess_index) # arrange all chess,隨機排列所有棋子
    # chess_index是一個陣列, 每個元素都會包含一個值,每個值會代表特定的棋子
    data_string = pickle.dumps( chess_index ) # 將棋盤狀態轉換成string發送到client端
    sc.sendall( data_string )

    for i in range(0, 4):
        for j in range(0, 4):
            ch = chess(chess_index[8*i+j], (i, j), chess_back.get_size())
            main_chess[i][j] = ch
            cor[i][j] = (ch.x, ch.y)
            main_map[i][j] = (i, j)
    for i in range(0, 4):
        for j in range(0, 4):
            ch = chess(chess_index[8*i+4+j], (i, 4+j), chess_back.get_size())
            main_chess[i][4+j] = ch
            cor[i][4+j] = (ch.x, ch.y)
            main_map[i][4+j] = (i, 4+j)
    
    # 將棋盤和棋子全部印到視窗上
    screen.blit(background, (0,0))
    screen.blit(new_game, (new_game_iconi, new_game_iconj))
    display_font()

    for cr in main_chess:
        for c in cr:
            c.draw(screen)

    pygame.display.update()

    # Test data
    #first = 0
    #com_color = 1
    #player_color = 0
    #turn_id = 1
    #back_num = 16
    ## chess_num[0] = 3
    ## chess_num[1] = 3
    #
    ##for i in range(0, 4):
    #for j in range(0, 8):
    #    main_chess[1][j].live = 0
    #    main_map[1][j] = None
    #
    #for i in range(0, 4):
    #    main_chess[i][5].live = 0
    #    main_map[i][5] = None
    #
    #ch = chess(5, (3, 2), chess_back.get_size())
    #ch.back = 0
    #ch.live = 1
    #main_chess[3][2] = ch
    #main_map[3][2] = (3, 2)
    #
    #ch = chess(0, (2, 2), chess_back.get_size())
    #ch.back = 0
    #ch.live = 1
    #main_chess[2][2] = ch
    #main_map[2][2] = (2, 2)
    #
    #ch = chess(1, (3, 3), chess_back.get_size())
    #ch.back = 0
    #ch.live = 1
    #main_chess[3][3] = ch
    #main_map[3][3] = (3, 3)
    #
    #ch = chess(2, (3, 1), chess_back.get_size())
    #ch.back = 0
    #ch.live = 1
    #main_chess[3][1] = ch
    #main_map[3][1] = (3, 1)
    #
    #ch = chess(30, (1, 5), chess_back.get_size())
    #ch.back = 0
    #ch.live = 1
    #main_chess[1][5] = ch
    #main_map[1][5] = (1, 5)
    #        
    #ch = chess(7, (3, 6), chess_back.get_size())
    #ch.back = 0
    #ch.live = 1
    #main_chess[3][6] = ch
    #main_map[3][6] = (3, 6)
    #
    #ch = chess(12, (1, 0), chess_back.get_size())
    #ch.back = 0
    #ch.live = 1
    #main_chess[1][0] = ch
    #main_map[1][0] = (1, 0)
    #End Test data

    while 0 == player_win:
        if 1 == game_start: # 開始一個新遊戲時要播放的特殊音效
            sound_new.play()
            game_start = 0 # 播放玩之後則不再標注為新遊戲


        no_move = 1
        if 2 == turn_id: # 處理移動棋子的階段(?)
            for cr in main_chess:
                for c in cr:
                    com_mv = 0
                    if c.x != cor[c.row][c.col][0]:   # x軸 當偵測到該棋子的圖像沒有在他本來該在的座標上,則開始逐步調整x的位置,以累加的方式讓過程以動畫呈現
                        c.x = c.x+1 if c.x < cor[c.row][c.col][0] else c.x-1 # 棋子圖片往x軸方向移動,+1或是-1
                        com_mv = 1
                        if (c.x, c.y) == cor[c.row][c.col]: # 棋子圖片已經到達指定位置
                            if main_map[c.row][c.col] != None: # 當指定位置原本已經有其他棋子在時,代表吃子的動作
                                (desti, destj) = main_map[c.row][c.col] # 記下該點的map位置
                                dest_ch = main_chess[desti][destj]      # 取得該map位置的棋子
                                dest_ch.live = 0                        # 將該旗子標示為未存活,代表已經被吃掉
                                chess_num[dest_ch.color] -= 1           # 該色棋子數量減一
                            main_map[c.row][c.col] = (com_mv_map[0], com_mv_map[1])
                            turn_id = host_color
                    if c.y != cor[c.row][c.col][1]:   # y軸 原理同上
                        c.y = c.y+1 if c.y < cor[c.row][c.col][1] else c.y-1
                        com_mv = 1  
                        if (c.x, c.y) == cor[c.row][c.col]:
                            if main_map[c.row][c.col] != None:
                                (desti, destj) = main_map[c.row][c.col]
                                dest_ch = main_chess[desti][destj]
                                dest_ch.live = 0
                                chess_num[dest_ch.color] -= 1
                            main_map[c.row][c.col] = (com_mv_map[0], com_mv_map[1])
                            turn_id = host_color
                    if 1 == com_mv: 
                        no_move = 0
                        c.draw(screen)
                        com_mv = 0
            if 1 == no_move:    # 動畫播放結束
                turn_id = host_color

        if selected_c != None:
            selected_c.move()
            selected_c.draw(screen)
      
        # chess_ai() 將ai的部份拿掉

        # 玩家二行動時的狀態


        if turn_id == player2_color:             # player2移動時的狀態,player2為client端,所以等待client端的傳來的資料
            if 0 == back_num and 1 == cant_move(main_map, main_chess, player2_color):
                print 'player2 cant move'
                player_win = 1

            if first == 1:  # 如果是第一回合,代表client端必須要告知他第一個抽中的顏色
                recv_data = sc.recv( 1 )
                pygame.event.clear() # # 為了確保沒有多餘的動作,每次接收資料之後先清除event
                if recv_data == '1':
                    player2_color = 1
                elif recv_data == '0':
                    player2_color = 0

                player_color = 1 - player2_color # player1的顏色會和player2相反
                host_color = player_color        # 紀錄本機端的顏色
                first = 0

            recv_data = sc.recv( MAX_BYTES)  # 從client端傳來的動作資料,此種資料有三種可能,翻開某個座標的棋,移動某個旗子到另一個棋子,投降
            pygame.event.clear() # # 為了確保沒有多餘的動作,每次接收資料之後先清除event

            if recv_data[0:4] == 'surr' or recv_data[0:4] == 'urr':   # 傳來投降的字串,client player2放棄比賽
                player_win = 1
            elif recv_data[0:4] == 'open':  # client翻開一顆覆蓋的棋子
                # 取得那個棋子的map位置
                map_i = int( recv_data[4:5], 10 ) 
                map_j = int( recv_data[5:6], 10 )
                main_chess[map_i][map_j].back = -1
                back_num -= 1
                turn_id = player_color
            elif recv_data[0:4] == 'move':   # 將棋子進行移動
                # 首先紀錄下要移動旗子的座標
                org = ( int( recv_data[4:5] ), int( recv_data[5:6] ) )
                dest = ( int( recv_data[6:7] ), int( recv_data[7:8] ) )
                main_map, main_chess = move_s( org, dest, main_map, main_chess )
                turn_id = 2                                                          # 移完棋子之後進入播放動畫的階段
            # XXXXXXXXX

        # 到此為只是player2行動的狀態

        # 接著是player1的狀態,必須將處理的玩家動作送到player2去

        if turn_id == player_color:
            if 0 == back_num and 1 == cant_move(main_map, main_chess, player_color):
                print 'player cant move'
                player_win = -1

            for event in pygame.event.get():
                if event.type == QUIT:
                    exit()
                elif event.type == pygame.MOUSEBUTTONDOWN and turn_id == player_color:     # 按下滑鼠的狀況
                    (mouseX, mouseY) = pygame.mouse.get_pos()
                    if new_game_iconi < mouseX < new_game_iconi + new_game.get_width() and new_game_iconj < mouseY < new_game_iconj + new_game.get_height(): # 按下投降記號,印出遊戲結果並開啟新遊戲
                        send_data = 'surr'
                        sc.sendall( send_data )
                        player_win = -1
                    main_map, main_chess = all_chess_move(main_map, main_chess) # 查出所有棋子可行的行動(不確定?)
                    sound_click.play()
                    click_once = 0             # 紀錄是否已經按了某個棋子的變數
                    for chr in main_chess:
                        for chc in chr:
                            if 0 == click_once: # 如果尚未按住某個棋子,則會根據點選位置的座標來判斷他是否會按到某個棋
                                ch_index = chc.click((mouseX, mouseY))
                                if ch_index != None: # 如果該座標可以找到棋子,代表玩家點選了一個棋子
                                    if 1 == player1_first and 1 == first:                            # 第一回合的情境,這個時候會判斷玩家弟一個選擇的棋子顏色,並將該顏色設定為玩家顏色
                                        turn_id = index_to_color(ch_index)                          # 之後變會將另一玩家顏色設定為相對的另一色
                                        player_color = turn_id
                                        sc.sendall( str( player_color ) )                           # 此外還要告知另一個玩家自己抽到的顏色
                                        host_color = player_color
                                        ( click_i, click_j ) = main_map[chc.row][chc.col]

                                        com_color = 1 - player_color
                                        player2_color = 1 - player_color
                                        first = 0                                                   # 取消第一回合的flag
                                        selected_c = None                                           # 由於第一回合所有旗子都必定是覆蓋的
                                        back_num -= 1
                                        send_data = 'open{}{}'.format( click_i, click_j )
                                        sc.sendall( send_data )
                                        turn_id = player2_color
                                    elif -1 == ch_index and chc.color == player_color:              # 棋子並非覆蓋,況且現在輪到player1,當棋子為非覆蓋的時候click會回傳-1
                                        selected_c = chc
                                    elif ch_index != -1 and 0 == first:                             # 棋子處於覆蓋的狀況,並且已經不是第一回合了
                                        ( click_i, click_j ) = main_map[chc.row][chc.col]
                                        selected_c = None
                                        back_num -= 1
                                        send_data = 'open{}{}'.format( click_i, click_j )
                                        sc.sendall( send_data )
                                        turn_id = player2_color
                                    click_once = 1
                                    break
                elif event.type == pygame.MOUSEBUTTONUP and turn_id == player_color:                # 回合輪到player1時放開滑鼠時的動作
                    if selected_c != None:
                        (mouseX, mouseY) = pygame.mouse.get_pos()
                        moving = 0
                        for pm in selected_c.possible_move:
                            if pm == mouse_position_to_block(mouseX, mouseY, chess_back):           # mouse_position_to_block將滑鼠位置轉換為棋盤位置的function
                                if main_map[pm[0]][pm[1]] != None:                                  # 當移動的目標不是空的位置時,代表要進行吃子的動作
                                    main_chess[main_map[pm[0]][pm[1]][0]][main_map[pm[0]][pm[1]][1]].live = 0
                                    chess_num[main_chess[main_map[pm[0]][pm[1]][0]][main_map[pm[0]][pm[1]][1]].color] -= 1
                                    sound_capture.play()
                                else:
                                    sound_move.play()
                                main_map[pm[0]][pm[1]] = main_map[selected_c.row][selected_c.col]   # 目標位置的棋子變為來源位置原本的旗子
                                main_map[selected_c.row][selected_c.col] = None                     # 來源位置的棋已經走了,標記為none
                                org = (selected_c.row, selected_c.col)
                                selected_c.x = cor[pm[0]][pm[1]][0]
                                selected_c.y = cor[pm[0]][pm[1]][1]
                                selected_c.row = pm[0]
                                selected_c.col = pm[1]
                                dest = (selected_c.row, selected_c.col)

                                send_data = 'move{}{}{}{}'.format( org[0], org[1], dest[0], dest[1] ) # 送出移動的座標!!!!!!!!!!!!!!!!!!!!!!
                                sc.sendall( send_data )

                                moving = 1
                                turn_id = player2_color
                                move_step[sindex] = [selected_c.color, org, dest]
                                #print move_step[sindex]
                                sindex = (sindex+1)%4

                                br = 0
                                while(br < len(break_long_capture_dest)):
                                    b = 0
                                    for d in break_long_capture_dest[br]:
                                        if dest == d:
                                            del break_long_capture_dest[br]
                                            del break_long_capture_org[br]
                                            del com_ban_step[br]
                                            b = 1
                                            break
                                    if 0 == b:
                                        br += 1
                                br = 0
                                while(br < len(break_long_capture_org)):
                                    b = 0
                                    for o in break_long_capture_org[br]:
                                        if org == o:
                                            del break_long_capture_dest[br]
                                            del break_long_capture_org[br]
                                            del com_ban_step[br]
                                            b = 1
                                            break
                                    if 0 == b:
                                        br += 1

                                break

                        if 0 == moving:
                           (selected_c.x, selected_c.y) = cor[selected_c.row][selected_c.col] 

                        selected_c.speed = 0
                        selected_c = None
                        moving = 1
                        break
                    else:
                        moving = 1
        
        if 1 == moving:
            main_map, main_chess = all_chess_move(main_map, main_chess)
            moving = 0
            
        if selected_c != None:                      # 此為按住棋子拖曳時的動畫呈現
            (mouseX, mouseY) = pygame.mouse.get_pos()
            dx = mouseX - selected_c.x
            dy = mouseY - selected_c.y
            dx -= selected_c.size[0]/2
            dy -= selected_c.size[1]/2
            selected_c.angle = 0.5*math.pi + math.atan2(dy, dx)
            selected_c.speed = math.hypot(dx, dy) * 0.1

        if 0 == chess_num[player_color]:
            player_win = -1

        elif 0 == chess_num[player2_color]:
            player_win = 1
            
        if 1 == player_win:
            screen.blit(background, (0,0))
            display_font()
            for cr in main_chess:
                for c in cr:
                    c.draw(screen)
            sound_win.play()
            pygame.display.update()
            time.sleep(5)
        elif -1 == player_win:
            screen.blit(background, (0,0))
            display_font()
            for cr in main_chess:
                for c in cr:
                    c.draw(screen)
            sound_loss.play()
            pygame.display.update()
            time.sleep(5)

        # 將棋盤,訊息,投降符號,棋子全部畫到螢幕上
        screen.blit(background, (0,0))
        screen.blit(new_game, (new_game_iconi, new_game_iconj))

        display_font()
        for cr in main_chess:
            for c in cr:
                c.draw(screen)
        pygame.display.update()
            
    exit()
    # end of server()

# =============================================================================================================

if __name__ == "__main__":
    choices = { 'client': client, 'server': server }
    parser = argparse.ArgumentParser( description = 'Play darkchess with remote rival' )
    parser.add_argument( 'role', choices=choices, help='which role to take' )
    parser.add_argument( 'host', help='interface the server listens at;host the client sends to' )
    parser.add_argument( '-p', metavar='PORT', type=int, default=1060, help='TCP port (default 1060)' )
    args = parser.parse_args()
    function = choices[args.role]
    function( args.host, args.p )
    main()
