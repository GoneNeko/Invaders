#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pygame
from pygame.locals import *
import codecs
import os
import random
import struct
import sys


sounds = {}
TITLE, FIELD, TALK, COMMAND = range(4)
SCR_RECT = Rect(0, 0, 600, 600)


def load_image(dir, file, colorkey=None):
    file = os.path.join(dir, file)
    image = pygame.image.load(file)
    image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0,0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image

def load_sound(filename):
    filename = os.path.join("data", filename)
    return pygame.mixer.Sound(filename)

def split_image(image, n):
    """横に長いイメージを同じ大きさのn枚のイメージに分割
    分割したイメージを格納したリストを返す"""
    image_list = []
    w = image.get_width()
    h = image.get_height()
    w1 = w / n
    for i in range(0, w, 22):
        surface = pygame.Surface((w1,h))
        surface.blit(image, (0,0), (i,0,w1,h))
        surface.set_colorkey(surface.get_at((0,0)), RLEACCEL)
        surface.convert()
        image_list.append(surface)
    return image_list

def collision_detection(player, aliens, shots, beams):
    """衝突判定"""
    # エイリアンとミサイルの衝突判定
    alien_collided = pygame.sprite.groupcollide(aliens, shots, True, True)
    for alien in list(alien_collided.keys()):
        Alien.randomize_sound.play()
    # プレイヤーとビームの衝突判定
    beam_collided = pygame.sprite.spritecollide(player, beams, True)
    if beam_collided:  # プレイヤーと衝突したビームがあれば
        Player.explosion_sound.play()
        # TODO: ゲームオーバー処理
    # ビームとミサイルの衝突判定
    beam_collided = pygame.sprite.groupcollide(beams, shots, True, True)
    for beam in list(alien_collided.keys()):
        beam.randomize_sound.play()


class MessageEngine:
    FONT_WIDTH = 16
    FONT_HEIGHT = 22
    WHITE, RED, GREEN, BLUE = 0, 160, 320, 480
    def __init__(self):
        self.image = load_image("data", "font.png", -1)
        self.color = self.WHITE
        self.kana2rect = {}
        self.create_hash()
    def set_color(self, color):
        """文字色をセット"""
        self.color = color
        # 変な値だったらWHITEにする
        if not self.color in [self.WHITE,self.RED,self.GREEN,self.BLUE]:
            self.color = self.WHITE
    def draw_character(self, screen, pos, ch):
        """1文字だけ描画する"""
        x, y = pos
        rect = self.kana2rect[ch]
        screen.blit(self.image, (x,y), (rect.x+self.color,rect.y,rect.width,rect.height))
    def draw_string(self, screen, pos, str):
        """文字列を描画"""
        x, y = pos
        for i, ch in enumerate(str):
            dx = x + self.FONT_WIDTH * i
            self.draw_character(screen, (dx,y), ch)
    def create_hash(self):
        """文字から座標への辞書を作成"""
        filepath = os.path.join("data", "kana2rect.dat")
        fp = codecs.open(filepath, "r", "utf-8")
        for line in fp.readlines():
            line = line.rstrip()
            d = line.split(" ")
            kana, x, y, w, h = d[0], int(d[1]), int(d[2]), int(d[3]), int(d[4])
            self.kana2rect[kana] = Rect(x, y, w, h)
        fp.close()


class Title:
    """タイトル画面"""
    START, CONTINUE, EXIT = 0, 1, 2
    def __init__(self, msg_engine):
        self.msg_engine = msg_engine
        self.title_img = load_image("data", "title.png", -1)
        self.cursor_img = load_image("data", "cursor2.png", -1)
        self.menu = self.START
        self.play_bgm()
    def update(self):
        pass
    def draw(self, screen):
        screen.fill((0,0,128))
        # タイトルの描画
        screen.blit(self.title_img, (20,60))
        # メニューの描画
        self.msg_engine.draw_string(screen, (260,260), u"ＳＴＡＲＴ")
        # self.msg_engine.draw_string(screen, (260,280), u"ＣＯＮＴＩＮＵＥ")
        self.msg_engine.draw_string(screen, (260,320), u"ＥＸＩＴ")
        # クレジットの描画
        self.msg_engine.draw_string(screen, (200,400), u"２０１9　あぷりかいはつ")
        # メニューカーソルの描画
        if self.menu == self.START:
            screen.blit(self.cursor_img, (240, 260))
        elif self.menu == self.EXIT:
            screen.blit(self.cursor_img, (240, 320))
    def play_bgm(self):
        bgm_file = "title.mp3"
        bgm_file = os.path.join("bgm", bgm_file)
        pygame.mixer.music.load(bgm_file)
        pygame.mixer.music.play(-1)

class PyRPG:
    def __init__(self):
        pygame.init()
        # フルスクリーン化 + Hardware Surface使用
        # self.screen = pygame.display.set_mode(SCR_RECT.size, DOUBLEBUF|HWSURFACE|FULLSCREEN)
        self.screen = pygame.display.set_mode(SCR_RECT.size)
        pygame.display.set_caption(u"Invaders")
        # サウンドをロード
        self.load_sounds("data", "sound.dat")
        # メッセージエンジン
        self.msg_engine = MessageEngine()
        # タイトル画面
        self.title = Title(self.msg_engine)
        # メインループを起動
        self.game_state = TITLE
        self.mainloop()
    def mainloop(self):
        """メインループ"""
        clock = pygame.time.Clock()
        while True:
            clock.tick(60)
            self.update()             # ゲーム状態の更新
            self.render()             # ゲームオブジェクトのレンダリング
            pygame.display.update()  # 画面に描画
            self.check_event()        # イベントハンドラ
    def update(self):
        """ゲーム状態の更新"""
        if self.game_state == TITLE:
            self.title.update()
        # elif self.game_state == FIELD:
        #     self.map.update()
        #     self.party.update(self.map)
        # elif self.game_state == TALK:
        #     self.msgwnd.update()
    def render(self):
        """ゲームオブジェクトのレンダリング"""
        if self.game_state == TITLE:
            self.title.draw(self.screen)
        # elif self.game_state == FIELD or self.game_state == TALK or self.game_state == COMMAND:
        #     offset = self.calc_offset(self.party.member[0])
        #     self.map.draw(self.screen, offset)
        #     self.party.draw(self.screen, offset)
        #     self.msgwnd.draw(self.screen)
        #     self.cmdwnd.draw(self.screen)
        #     self.show_info()  # デバッグ情報を画面に表示
    def check_event(self):
        """イベントハンドラ"""
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()
            # 表示されているウィンドウに応じてイベントハンドラを変更
            if self.game_state == TITLE:
                self.title_handler(event)
            # elif self.game_state == FIELD:
            #     self.field_handler(event)
            # elif self.game_state == COMMAND:
            #     self.cmd_handler(event)
            # elif self.game_state == TALK:
            #     self.talk_handler(event)
    def title_handler(self, event):
        """タイトル画面のイベントハンドラ"""
        if event.type == KEYUP and event.key == K_UP:
            self.title.menu -= 1
            if self.title.menu < 0:
                self.title.menu = 0
        elif event.type == KEYDOWN and event.key == K_DOWN:
            self.title.menu += 1
            if self.title.menu > 2:
                self.title.menu = 2
        if event.type == KEYDOWN and event.key == K_SPACE:
            sounds["pi"].play()
            if self.title.menu == Title.START:
                pygame.init()
                screen = pygame.display.set_mode(SCR_RECT.size)
                pygame.display.set_caption("Invader 05 エイリアンの反撃")
                # サウンドのロード
                Alien.randomize_sound = load_sound("randomize.wav")
                Player.shoot_sound = load_sound("shoot.wav")
                Player.explosion_sound = load_sound("explosion.wav")
                # スプライトグループを作成して登録
                all = pygame.sprite.RenderUpdates()
                aliens = pygame.sprite.Group()  # エイリアングループ
                shots = pygame.sprite.Group()   # ミサイルグループ
                beams = pygame.sprite.Group()   # ビームグループ
                Player.containers = all
                Shot.containers = all, shots
                Alien.containers = all, aliens
                Beam.containers = all, beams


                # スプライトの画像を登録--ここをいじって画像を変える
                Back_image = load_image("data", "universe.png", -1)
                back_rect = Back_image.get_rect()
                Player.image = load_image("data", "player.png", -1)
                Shot.image = load_image("data", "beam_b.png", -1)
                Alien.images = split_image(load_image("data", "enemy.png", -1), 2)
                Beam.image = load_image("data", "beam_r.png", -1)

                # 自機を作成
                player = Player()

                # エイリアンを作成--ここをいじってエイリアンの位置を替える
                for i in range(0, 50):
                    x = 20 + (i % 10) * 40
                    y = 20 + (i - 25) * (i - 25) / 3
                    Alien((x,y))

                clock = pygame.time.Clock()
                while True:
                    clock.tick(60)
                    all.update()
                    # ミサイルとエイリアンの衝突判定
                    collision_detection(player, aliens, shots, beams)
                    all.draw(screen)
                    pygame.display.update()
                    for event in pygame.event.get():
                        if event.type == QUIT:
                            pygame.quit()
                            sys.exit()
                        elif event.type == KEYDOWN and event.key == K_ESCAPE:
                            pygame.quit()
                            sys.exit()
                    screen.blit(Back_image, back_rect)

            elif self.title.menu == Title.CONTINUE:
                pass
            elif self.title.menu == Title.EXIT:
                pygame.quit()
                sys.exit()
    def load_sounds(self, dir, file):
        """サウンドをロードしてsoundsに格納"""
        file = os.path.join(dir, file)
        fp = open(file, "r")
        for line in fp:
            line = line.rstrip()
            data = line.split(",")
            se_name = data[0]
            se_file = os.path.join("se", data[1])
            sounds[se_name] = pygame.mixer.Sound(se_file)
        fp.close()

class Player(pygame.sprite.Sprite):
    """自機"""
    speed = 5  # 移動速度
    reload_time = 15  # リロード時間
    def __init__(self):
        # imageとcontainersはmain()でセット
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.rect = self.image.get_rect()
        self.rect.bottom = SCR_RECT.bottom  # プレイヤーが画面の一番下
        self.reload_timer = 0
    def update(self):
        # 押されているキーをチェック
        pressed_keys = pygame.key.get_pressed()
        # 押されているキーに応じてプレイヤーを移動
        if pressed_keys[K_LEFT]:
            self.rect.move_ip(-self.speed, 0)
        elif pressed_keys[K_RIGHT]:
            self.rect.move_ip(self.speed, 0)
        elif pressed_keys[K_UP]:
            self.rect.move_ip(0, -self.speed)
        elif pressed_keys[K_DOWN]:
            self.rect.move_ip(0, self.speed)
        self.rect.clamp_ip(SCR_RECT)
        # ミサイルの発射
        if pressed_keys[K_SPACE]:
            # リロード時間が0になるまで再発射できない
            if self.reload_timer > 0:
                # リロード中
                self.reload_timer -= 1
            else:
                # 発射！！！
                Player.shoot_sound.play()
                Shot(self.rect.center)  # 作成すると同時にallに追加される
                self.reload_timer = self.reload_time

class Alien(pygame.sprite.Sprite):
    """エイリアン"""
    speed = 2  # 移動速度
    animcycle = 18  # アニメーション速度
    frame = 0
    move_width = 230  # 横方向の移動範囲
    prob_beam = 0.0005  # ビームを発射する確率
    def __init__(self, pos):
        # imagesとcontainersはmain()でセット
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.left = pos[0]  # 移動できる左端
        self.right = self.left + self.move_width  # 移動できる右端
    def update(self):
        # 横方向への移動
        self.rect.move_ip(self.speed, 0)
        if self.rect.center[0] < self.left or self.rect.center[0] > self.right:
            self.speed = -self.speed
        # ビームを発射--ここをいじってビームが降ってくる個数を変える
        if random.random() < self.prob_beam:
            Beam(self.rect.center)
        self.image = self.images[self.frame//self.animcycle%2]

class Shot(pygame.sprite.Sprite):
    """プレイヤーが発射するミサイル"""
    speed = 9  # 移動速度
    def __init__(self, pos):
        # imageとcontainersはmain()でセット
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.rect = self.image.get_rect()
        self.rect.center = pos  # 中心座標をposに
    def update(self):
        self.rect.move_ip(0, -self.speed)  # 上へ移動
        if self.rect.top < 0:  # 上端に達したら除去
            self.kill()

class Beam(pygame.sprite.Sprite):
    """エイリアンが発射するビーム"""
    speed = 5  # 移動速度
    def __init__(self, pos):
        # imageとcontainersはmain()でセット
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.rect = self.image.get_rect()
        self.rect.center = pos
    def update(self):
        self.rect.move_ip(0, self.speed)  # 下へ移動
        if self.rect.bottom > SCR_RECT.height:  # 下端に達したら除去
            self.kill()



if __name__ == "__main__":
    PyRPG()

"""ライフポイントをつける
制限時間を設ける
コンテニュー機能をつける
タイトルのカーソルがうまくいかない
"""
