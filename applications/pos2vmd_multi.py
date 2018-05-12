#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# pos2vmd.py - convert joint position data to VMD

from __future__ import print_function

def usage(prog):
    print('usage: ' + prog + ' POSITION_FILE VMD_FILE')
    sys.exit()

import re
from PyQt5.QtGui import QQuaternion, QVector3D
from VmdWriter import VmdBoneFrame, VmdInfoIk, VmdShowIkFrame, VmdWriter
import argparse
import logging
import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def positions_to_frames(pos, frame=0, uxangle=0, lxangle=0, head_rotation=None, expression_frames=None):
    logger.info("output frame={0}".format(str(frame)))

	# 補正角度のクォータニオン
    upper_correctqq = QQuaternion.fromEulerAngles(QVector3D(uxangle, 0, 0))
    lower_correctqq = QQuaternion.fromEulerAngles(QVector3D(lxangle, 0, 0))

    """convert positions to bone frames"""
    frames = []
    # 上半身
    bf = VmdBoneFrame(frame)
    bf.name = b'\x8f\xe3\x94\xbc\x90\x67' # '上半身'
    direction = pos[8] - pos[7]
    up = QVector3D.crossProduct(direction, (pos[14] - pos[11])).normalized()
    upper_body_orientation = QQuaternion.fromDirection(direction, up)
    initial = QQuaternion.fromDirection(QVector3D(0, 1, 0), QVector3D(0, 0, 1))
    # 補正をかけて回転する
    bf.rotation = upper_correctqq * upper_body_orientation * initial.inverted()

    frames.append(bf)
    upper_body_rotation = bf.rotation
    
    # 下半身
    bf = VmdBoneFrame(frame)
    bf.name = b'\x89\xba\x94\xbc\x90\x67' # '下半身'
    direction = pos[0] - pos[7]
    up = QVector3D.crossProduct(direction, (pos[4] - pos[1]))
    lower_body_orientation = QQuaternion.fromDirection(direction, up)
    initial = QQuaternion.fromDirection(QVector3D(0, -1, 0), QVector3D(0, 0, 1))
    bf.rotation = lower_correctqq * lower_body_orientation * initial.inverted()
    lower_body_rotation = bf.rotation
    frames.append(bf)

    # logger.debug("下半身 bf.rotation")
    # logger.debug(bf.rotation)
    # logger.debug(bf.rotation.toEulerAngles())

    # 首は回転させず、頭のみ回転させる
    # 頭
    bf = VmdBoneFrame(frame)
    bf.name = b'\x93\xaa' # '頭'
    if head_rotation is None:
        # logger.debug("head_rotation is None")
        direction = pos[10] - pos[9]
        # direction = pos[10] - pos[8]
        up = QVector3D.crossProduct((pos[9] - pos[8]), (pos[10] - pos[9]))
        orientation = QQuaternion.fromDirection(direction, up)
        initial_orientation = QQuaternion.fromDirection(QVector3D(0, 1, 0), QVector3D(1, 0, 0))
        rotation = upper_correctqq * orientation * initial_orientation.inverted()
        bf.rotation = upper_body_rotation.inverted() * rotation
    else:
        bf.rotation = upper_correctqq * upper_body_rotation.inverted() * head_rotation
    frames.append(bf)
        
    # 左腕
    bf = VmdBoneFrame(frame)
    bf.name = b'\x8d\xb6\x98\x72' # '左腕'
    direction = pos[12] - pos[11]
    up = QVector3D.crossProduct((pos[12] - pos[11]), (pos[13] - pos[12]))
    orientation = QQuaternion.fromDirection(direction, up)
    initial_orientation = QQuaternion.fromDirection(QVector3D(1.73, -1, 0), QVector3D(1, 1.73, 0))
    rotation = upper_correctqq * orientation * initial_orientation.inverted()
    # 左腕ポーンの回転から親ボーンの回転を差し引いてbf.rotationに格納する。
    # upper_body_rotation * bf.rotation = rotation なので、
    bf.rotation = upper_body_rotation.inverted() * rotation
    left_arm_rotation = bf.rotation # 後で使うので保存しておく
    frames.append(bf)
    
    # 左ひじ
    bf = VmdBoneFrame(frame)
    bf.name = b'\x8d\xb6\x82\xd0\x82\xb6' # '左ひじ'
    direction = pos[13] - pos[12]
    up = QVector3D.crossProduct((pos[12] - pos[11]), (pos[13] - pos[12]))
    orientation = QQuaternion.fromDirection(direction, up)
    initial_orientation = QQuaternion.fromDirection(QVector3D(1.73, -1, 0), QVector3D(1, 1.73, 0))
    rotation = orientation * initial_orientation.inverted()
    # ひじはX軸補正しない(Y軸にしか曲がらないから)
    # 左ひじポーンの回転から親ボーンの回転を差し引いてbf.rotationに格納する。
    # upper_body_rotation * left_arm_rotation * bf.rotation = rotation なので、
    bf.rotation = left_arm_rotation.inverted() * upper_body_rotation.inverted() * rotation
    # bf.rotation = (upper_body_rotation * left_arm_rotation).inverted() * rotation # 別の表現
    frames.append(bf)

    
    # 右腕
    bf = VmdBoneFrame(frame)
    bf.name = b'\x89\x45\x98\x72' # '右腕'
    direction = pos[15] - pos[14]
    up = QVector3D.crossProduct((pos[15] - pos[14]), (pos[16] - pos[15]))
    orientation = QQuaternion.fromDirection(direction, up)
    initial_orientation = QQuaternion.fromDirection(QVector3D(-1.73, -1, 0), QVector3D(1, -1.73, 0))
    rotation = upper_correctqq * orientation * initial_orientation.inverted()
    bf.rotation = upper_body_rotation.inverted() * rotation
    right_arm_rotation = bf.rotation
    frames.append(bf)
    
    # 右ひじ
    bf = VmdBoneFrame(frame)
    bf.name = b'\x89\x45\x82\xd0\x82\xb6' # '右ひじ'
    direction = pos[16] - pos[15]
    up = QVector3D.crossProduct((pos[15] - pos[14]), (pos[16] - pos[15]))
    orientation = QQuaternion.fromDirection(direction, up)
    initial_orientation = QQuaternion.fromDirection(QVector3D(-1.73, -1, 0), QVector3D(1, -1.73, 0))
    # ひじはX軸補正しない(Y軸にしか曲がらないから)
    rotation = orientation * initial_orientation.inverted()
    bf.rotation = right_arm_rotation.inverted() * upper_body_rotation.inverted() * rotation
    frames.append(bf)

    # 左足
    bf = VmdBoneFrame(frame)
    bf.name = b'\x8d\xb6\x91\xab' # '左足'
    direction = pos[5] - pos[4]
    up = QVector3D.crossProduct((pos[5] - pos[4]), (pos[6] - pos[5]))
    orientation = QQuaternion.fromDirection(direction, up)
    initial_orientation = QQuaternion.fromDirection(QVector3D(0, -1, 0), QVector3D(-1, 0, 0))
    rotation = lower_correctqq * orientation * initial_orientation.inverted()
    bf.rotation = lower_body_rotation.inverted() * rotation
    left_leg_rotation = bf.rotation
    frames.append(bf)
    
    # 左ひざ
    bf = VmdBoneFrame(frame)
    bf.name = b'\x8d\xb6\x82\xd0\x82\xb4' # '左ひざ'
    direction = pos[6] - pos[5]
    up = QVector3D.crossProduct((pos[5] - pos[4]), (pos[6] - pos[5]))
    orientation = QQuaternion.fromDirection(direction, up)
    initial_orientation = QQuaternion.fromDirection(QVector3D(0, -1, 0), QVector3D(-1, 0, 0))
    rotation = lower_correctqq * orientation * initial_orientation.inverted()
    bf.rotation = left_leg_rotation.inverted() * lower_body_rotation.inverted() * rotation
    frames.append(bf)

    # 右足
    bf = VmdBoneFrame(frame)
    bf.name = b'\x89\x45\x91\xab' # '右足'
    direction = pos[2] - pos[1]
    up = QVector3D.crossProduct((pos[2] - pos[1]), (pos[3] - pos[2]))
    orientation = QQuaternion.fromDirection(direction, up)
    initial_orientation = QQuaternion.fromDirection(QVector3D(0, -1, 0), QVector3D(-1, 0, 0))
    rotation = lower_correctqq * orientation * initial_orientation.inverted()
    bf.rotation = lower_body_rotation.inverted() * rotation
    right_leg_rotation = bf.rotation
    frames.append(bf)
    
    # 右ひざ
    bf = VmdBoneFrame(frame)
    bf.name = b'\x89\x45\x82\xd0\x82\xb4' # '右ひざ'
    direction = pos[3] - pos[2]
    up = QVector3D.crossProduct((pos[2] - pos[1]), (pos[3] - pos[2]))
    orientation = QQuaternion.fromDirection(direction, up)
    initial_orientation = QQuaternion.fromDirection(QVector3D(0, -1, 0), QVector3D(-1, 0, 0))
    rotation = lower_correctqq * orientation * initial_orientation.inverted()
    bf.rotation = right_leg_rotation.inverted() * lower_body_rotation.inverted() * rotation
    frames.append(bf)

    return frames

def make_showik_frames():
    frames = []
    sf = VmdShowIkFrame()
    sf.show = 1
    sf.ik.append(VmdInfoIk(b'\x8d\xb6\x91\xab\x82\x68\x82\x6a', 0)) # '左足ＩＫ'
    sf.ik.append(VmdInfoIk(b'\x89\x45\x91\xab\x82\x68\x82\x6a', 0)) # '右足ＩＫ'
    sf.ik.append(VmdInfoIk(b'\x8d\xb6\x82\xc2\x82\xdc\x90\xe6\x82\x68\x82\x6a', 0)) # '左つま先ＩＫ'
    sf.ik.append(VmdInfoIk(b'\x89\x45\x82\xc2\x82\xdc\x90\xe6\x82\x68\x82\x6a', 0)) # '右つま先ＩＫ'
    frames.append(sf)
    return frames

def read_positions(position_file):
    """Read joint position data"""
    f = open(position_file, "r")

    positions = []
    while True:
        line = f.readline()
        if not line:
            break
        line = line.rstrip('\r\n')
        a = re.split(' ', line)
        # 元データはz軸が垂直上向き。MMDに合わせるためにyとzを入れ替える。
        q = QVector3D(float(a[1]), float(a[3]), float(a[2])) # a[0]: index
        positions.append(q) # a[0]: index
    f.close()
    return positions

#複数フレームの読み込み
def read_positions_multi(position_file):
    """Read joint position data"""
    f = open(position_file, "r")

    positions = []
    while True:
        line = f.readline()
        if not line:
            break
        line = line.rstrip('\n')

        # 一旦カンマで複数行に分解
        inposition = []
        for inline in re.split(",\s*", line):
            if inline:
                # 1フレーム分に分解したら、空白で分解
                a = re.split(' ', inline)
                # print(a)
                # 元データはz軸が垂直上向き。MMDに合わせるためにyとzを入れ替える。
                q = QVector3D(float(a[1]), float(a[3]), float(a[2])) # a[0]: index
                inposition.append(q) # a[0]: index
        
        positions.append(inposition)
    f.close()
    return positions

def convert_position(pose_3d):
    positions = []
    for pose in pose_3d:
        for j in range(pose.shape[1]):
            q = QVector3D(pose[0, j], pose[2, j], pose[1, j])
            positions.append(q)
    return positions
    
def position_list_to_vmd(positions, vmd_file, head_rotation=None, expression_frames=None):
    bone_frames = []
    bf = positions_to_frames(positions, head_rotation)
    bone_frames.extend(bf)
    showik_frames = make_showik_frames()
    writer = VmdWriter()
    # writer.write_vmd_file(vmd_file, bone_frames, showik_frames, expression_frames)
    writer.write_vmd_file(vmd_file, bone_frames, showik_frames)

def position_list_to_vmd_multi(positions_multi, vmd_file, uxangle=0, lxangle=0, head_rotation_list=None, expression_frames_list=None):
    writer = VmdWriter()
    
    bone_frames = []
    for frame, positions in enumerate(positions_multi):
        
        if head_rotation_list is None:
            head_rotation = None
        else:
            head_rotation = head_rotation_list[frame]
        
        if expression_frames_list is None:
            expression_frames = None
        else:
            expression_frames = expression_frames_list[frame]

        bf = positions_to_frames(positions, frame, uxangle, lxangle, head_rotation, expression_frames)
        bone_frames.extend(bf)
    
    showik_frames = make_showik_frames()
    # writer.write_vmd_file(vmd_file, bone_frames, showik_frames, expression_frames)
    writer.write_vmd_file(vmd_file, bone_frames, showik_frames)

def pos2vmd(pose_3d, vmd_file, head_rotation=None, expression_frames=None):
    positions = convert_position(pose_3d)
    position_list_to_vmd(positions, vmd_file, head_rotation, expression_frames)
    
def pos2vmd_multi(pose_3d_list, vmd_file, head_rotation_list=None, expression_frames_list=None):
    positions_multi = []

    for pose_3d in pose_3d_list:
        positions = convert_position(pose_3d)
        positions_multi.append(positions)

    position_list_to_vmd_multi(positions_multi, vmd_file, 0, head_rotation_list, expression_frames_list)
    
def position_file_to_vmd(position_file, vmd_file):
    positions = read_positions(position_file)
    position_list_to_vmd(positions, vmd_file)
    
def position_multi_file_to_vmd(position_file, vmd_file, uxangle=0, lxangle=0, head_rotation_list=None, expression_frames_list=None):
    positions_multi = read_positions_multi(position_file)
    position_list_to_vmd_multi(positions_multi, vmd_file, uxangle, lxangle, head_rotation_list, expression_frames_list)
    
if __name__ == '__main__':
    import sys
    if (len(sys.argv) < 2):
        usage(sys.argv[0])

    parser = argparse.ArgumentParser(description='3d-pose-baseline to vmd')
    parser.add_argument('-t', '--target', dest='target', type=str,
                        help='target directory')
    parser.add_argument('-v', '--verbose', dest='verbose', type=int,
                        default=2,
                        help='loggin level')
    parser.add_argument('-u', '--upper-x-angle', dest='uxangle', type=int,
                        default=0,
                        help='global upper x angle correction')
    parser.add_argument('-l', '--lower-x-angle', dest='lxangle', type=int,
                        default=0,
                        help='global lower x angle correction')
    args = parser.parse_args()

    # resultディレクトリだけ指定させる
    base_dir = args.target

    # 入力と出力のファイル名は固定
    position_file = base_dir + "/pos.txt"
    vmd_file = "{0}/output_{1:%Y%m%d_%H%M%S}.vmd".format(base_dir, datetime.datetime.now())

    level = {0:logging.ERROR,
             1:logging.WARNING,
             2:logging.INFO,
             3:logging.DEBUG}

    # ログレベル設定
    logger.setLevel(level[args.verbose])

    # if os.path.exists('predictor/shape_predictor_68_face_landmarks.dat'):
    #     head_rotation = 

    position_multi_file_to_vmd(position_file, vmd_file, args.uxangle, args.lxangle)

    logger.info("VMDファイル出力完了: {0}".format(vmd_file))