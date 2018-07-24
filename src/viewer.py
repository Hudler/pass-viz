import arcade
import pandas as pd
import numpy as np
from collections import defaultdict
import argparse

PITCH_W = 680
PITCH_L = 1050
OFFSET = 50

class Field(arcade.Window):

    def __init__(self, players_file, mode, predictions, output_file):

        super().__init__(PITCH_L+2*OFFSET, PITCH_W+2*OFFSET, "MLSA 2018 Pass Prediction Challenge")

        self.players = pd.read_csv(players_file)
        self.players_list = []

        self.prev_example = None
        self.cur_example = 0
        self.next_example = ''

        self.passes_list = []

        if mode == 'V':
            self.predictions = np.load(predictions)

        self.mode = mode

        self.output_file = output_file

        self.hits = {}
        self.guesses = defaultdict(set)

        arcade.set_background_color(arcade.color.AMAZON)


    def setup(self):
        for pid in range(0,22):
            color = arcade.color.BLUE if pid < 11 else arcade.color.RED
            player = Player(pid, self.players[f'x_{pid}'].values, self.players[f'y_{pid}'].values, color)
            self.players_list.append(player)

        if self.mode == 'V':
            for pid in range(11):
                self.passes_list.append(Pass(self.players.Sx, self.players.Sy,
                                            self.players[f'x_{pid}'], self.players[f'y_{pid}'],
                                            arcade.color.YELLOW,
                                            self.predictions[:,pid]))
        elif self.mode == 'P':
            self.p = Pass(self.players.Sx, self.players.Sy, self.players.Rx, self.players.Ry, hidden=True)


    def on_draw(self):
        arcade.start_render()
        arcade.set_viewport(-OFFSET, PITCH_L+OFFSET, -OFFSET, PITCH_W+OFFSET)

        point_list = ((0, 0),
                      (0, PITCH_W),
                      (PITCH_L, PITCH_W),
                      (PITCH_L,0))

        arcade.draw_polygon_outline(point_list, arcade.color.WHITE, 3)

        arcade.draw_line(PITCH_L/2, 0, PITCH_L/2, PITCH_W, arcade.color.WHITE, 3)

        R = 9.15
        arcade.draw_points([(PITCH_L/2, PITCH_W/2)], arcade.color.WHITE, 5)
        arcade.draw_circle_outline(PITCH_L/2, PITCH_W/2, R*10, arcade.color.WHITE, 3)

        SMAL_BOX_W = (7.32/2 + 5.5) * 2
        SMAL_BOX_L = 5.5

        point_list = ((0, PITCH_W/2+(SMAL_BOX_W/2)*10),
                      (SMAL_BOX_L*10, PITCH_W/2+(SMAL_BOX_W/2)*10),
                      (SMAL_BOX_L*10, PITCH_W/2-(SMAL_BOX_W/2)*10),
                      (0, PITCH_W/2-(SMAL_BOX_W/2)*10))
        arcade.draw_polygon_outline(point_list, arcade.color.WHITE, 3)

        point_list = ((PITCH_L, PITCH_W/2+(SMAL_BOX_W/2)*10),
                      (PITCH_L-SMAL_BOX_L*10, PITCH_W/2+(SMAL_BOX_W/2)*10),
                      (PITCH_L-SMAL_BOX_L*10, PITCH_W/2-(SMAL_BOX_W/2)*10),
                      (PITCH_L, PITCH_W/2-(SMAL_BOX_W/2)*10)
                     )
        arcade.draw_polygon_outline(point_list, arcade.color.WHITE, 3)

        LARGE_BOX_W = 40.3
        LARGE_BOX_L = 16.5

        point_list = ((0, PITCH_W/2+(LARGE_BOX_W/2)*10),
                      (LARGE_BOX_L*10, PITCH_W/2+(LARGE_BOX_W/2)*10),
                      (LARGE_BOX_L*10, PITCH_W/2-(LARGE_BOX_W/2)*10),
                      (0, PITCH_W/2-(LARGE_BOX_W/2)*10))
        arcade.draw_polygon_outline(point_list, arcade.color.WHITE, 3)

        point_list = ((PITCH_L, PITCH_W/2+(LARGE_BOX_W/2)*10),
                      (PITCH_L-LARGE_BOX_L*10, PITCH_W/2+(LARGE_BOX_W/2)*10),
                      (PITCH_L-LARGE_BOX_L*10, PITCH_W/2-(LARGE_BOX_W/2)*10),
                      (PITCH_L, PITCH_W/2-(LARGE_BOX_W/2)*10)
                     )
        arcade.draw_polygon_outline(point_list, arcade.color.WHITE, 3)

        arcade.draw_points([(11*10, PITCH_W/2), (PITCH_L-11*10, PITCH_W/2)], arcade.color.WHITE, 5)

        for player in self.players_list:
            player.draw()

        if self.mode == 'V':
            for passline in self.passes_list:
                passline.draw()
        elif self.mode == 'P':
            self.p.draw()

            top1 = (pd.Series(self.hits) <= 1).mean()
            top2 = (pd.Series(self.hits) <= 2).mean()
            top3 = (pd.Series(self.hits) <= 3).mean()
            mrr = (1/pd.Series(self.hits)).mean()

            arcade.draw_text(f'MRR: {mrr:.2}, top 1/2/3: {top1:.2}/{top2:.2}/{top3:.2}',
                            30, PITCH_W-30, arcade.color.WHITE, 12)

            arcade.draw_text(f'example {self.cur_example}',
                            PITCH_L-170, PITCH_W-30, arcade.color.WHITE, 12)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.RIGHT:
            self.cur_example = (self.cur_example+1) % len(self.players)
        elif key == arcade.key.LEFT:
            self.cur_example = (self.cur_example-1) % len(self.players)
        elif key == arcade.key.ENTER:
            if self.next_example != '':
                if int(self.next_example) < len(self.players):
                    self.cur_example = int(self.next_example)
                self.next_example = ''
        elif key == arcade.key.UP:
            self.p.hidden = False
        elif key == arcade.key.DOWN:
            self.p.hidden = True
        else:
            self.next_example += str(key%48)


    def on_mouse_press(self, x, y, button, modifiers):
        x = x-OFFSET
        y = y-OFFSET
        if button == arcade.MOUSE_BUTTON_LEFT:
            min_dist = np.inf
            nearest = None
            tid = self.players.St.values[self.cur_example] * 11
            for player in self.players_list[tid:tid+11]:
                d = (player.x - x)**2 + (player.y - y)**2
                if  d < min_dist:
                    min_dist = d
                    nearest = player.pid

            self.guesses[self.cur_example].add(nearest)
            if self.players.R.values[self.cur_example] in self.guesses[self.cur_example]:
                self.hits[self.cur_example] = len(self.guesses[self.cur_example])
                if self.output_file:
                    pd.Series(self.hits).to_csv(self.output_file)
                self.cur_example += 1


    def update(self, dt):

        for player in self.players_list:
            if player.pid in self.guesses[self.cur_example]:
                color = arcade.color.GREEN
            elif player.pid == self.players.S.values[self.cur_example]:
                color = arcade.color.YELLOW
            else:
                color = player.orig_color
            player.update(self.cur_example,color)

        if self.mode == 'V':
            for R, passline in enumerate(self.passes_list):
                if R == self.players.R.values[self.cur_example]:
                    color = arcade.color.RED
                else:
                    color = arcade.color.YELLOW
                passline.update(self.cur_example, color)
        if self.mode == 'P':
            self.p.update(self.cur_example)


class Player:

    def __init__(self,pid,x,y,color):
        self.x_hist = (x+5250)/10
        self.y_hist = (y+3400)/10
        self.pid = pid
        self.orig_color = color
        self.color = color
        self.x = self.x_hist[0]
        self.y = self.y_hist[0]

    def update(self, idx, color):
        self.x = self.x_hist[idx]
        self.y = self.y_hist[idx]
        self.color = color

    def draw(self):
        arcade.draw_text(f'{self.pid}', self.x+5, self.y+5, arcade.color.WHITE, 10)
        arcade.draw_points([(self.x,self.y)], self.color, 10)

class Pass:

    def __init__(self,sender_x, sender_y, receiver_x, receiver_y, hidden=False, color=arcade.color.YELLOW, pred_hist=np.ones(10000)):
        self.hidden = hidden
        self.color = color
        self.orig_color = color
        self.pred_hist = pred_hist
        self.pred = 1
        self.Sx_hist = (sender_x+5250)/10
        self.Sy_hist = (sender_y+3400)/10
        self.Rx_hist = (receiver_x+5250)/10
        self.Ry_hist = (receiver_y+3400)/10

        self.Sx = self.Sx_hist[0]
        self.Sy = self.Sy_hist[0]
        self.Rx = self.Rx_hist[0]
        self.Ry = self.Ry_hist[0]

    def update(self, idx, color=arcade.color.YELLOW):
        self.color = color
        self.pred = self.pred_hist[idx]
        if self.hidden or self.pred == -1:
            self.Sx = -100
            self.Sy = -100
            self.Rx = -100
            self.Ry = -100
        else:
            self.Sx = self.Sx_hist[idx]
            self.Sy = self.Sy_hist[idx]
            self.Rx = self.Rx_hist[idx]
            self.Ry = self.Ry_hist[idx]

    def draw(self):
        arcade.draw_line(self.Sx, self.Sy, self.Rx, self.Ry, self.color, 5*abs(self.pred) )
        arcade.draw_circle_filled(self.Rx, self.Ry, 5*abs(self.pred), self.color)
        arcade.draw_text(f'{self.pred:.2f}', (self.Sx+self.Rx)/2, (self.Sy+self.Ry)/2, self.color, 10)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode',                       default='P')
    parser.add_argument('--data',                       default='../data/example_data.csv')
    parser.add_argument('--preds',                      default=None)
    parser.add_argument('--out',                        default=None)
    args = parser.parse_args()

    window = Field(players_file=args.data, mode=args.mode, predictions=args.preds, output_file=args.out)
    window.setup()
    arcade.run()
