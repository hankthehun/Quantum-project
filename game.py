from graph import *
from quantum import *


def get_move_render_position(x, y, index):
    column = index//5
    row = index%5
    return x + row*40, y + column*40


class GameInstance:
    def __init__(self, world, circuit=None):
        self.world = world
        if circuit is None:
            self.circuit = GameCircuit(self.world.get_qubit_amount())
        else:
            self.circuit = circuit
        self.current_moves = None
        self.selected_move = None
        self.confirmed = False
        self.confirm_button = None
        self.should_continue = False
        self.current_player = 0
        self.next_step_button = None

    def confirm(self):
        self.confirmed = True

    def stop(self):
        self.should_continue = False

    def reset_confirmation(self):
        self.confirmed = False
        if self.confirm_button is not None:
            self.confirm_button.destroy()
            self.confirm_button = None

    def ask_for_confirmation(self):
        if self.confirm_button is None:
            self.confirm_button = Button(self.world.root, text="Confirm", command=lambda: self.confirm())
            self.confirm_button.pack()

    def render_moves(self):
        self.world.canvas.delete("move")
        self.world.canvas.create_text(130, 670, text="Available Gates", font=("Helvetica", 12, "bold"), fill="black", tags="move")
        for i, move in enumerate(self.current_moves):
            x, y = get_move_render_position(50, 700, i)
            move.render(self.world.canvas, x, y, lambda m: self.select_move(m))
        self.world.root.update()

    def select_move(self, move):
        if move.selected:
            return
        self.world.allow_selection(True, self.current_player)
        self.selected_move = move
        for m in self.current_moves:
            m.selected = m == move
        self.render_moves()

    def execute_move(self, move):
        self.circuit.apply_single_gate(move.gate, self.world.get_selected_country().qubits[0])
        self.current_moves.remove(move)
        self.selected_move = None
        self.world.allow_selection(False)
        self.world.render()
        self.reset_confirmation()


    def wait_for_country_selected(self):
        if not self.should_continue:
            self.world.root.after(1, self.place_troops_iteration)
            return

        if self.world.selection.strip() != "":
            self.ask_for_confirmation()
            if self.confirmed:
                self.execute_move(self.selected_move)
                self.world.root.after(1, self.place_troops_iteration)
            else:
                self.world.root.after(50, self.wait_for_country_selected)

        else:
            self.world.root.after(50, self.wait_for_country_selected)


    def place_troops_iteration(self):
        if len(self.current_moves) <= 0:
            self.should_continue = False

        if self.should_continue:
            self.render_moves()
            self.wait_for_country_selected()
        else:
            self.next_step_button.destroy()
            self.next_step_button = None
            self.switch_player()
            self.place_troops()


    def place_troops(self):
        self.world.allow_selection(False)
        self.world.selection = ""
        self.world.render()
        self.world.canvas.delete("turn")
        self.world.canvas.create_text(self.world.size // 2, 20, text="Phase 1 : Place Troops", font=("Helvetica", 20), fill=COLORS[self.current_player], tags="turn")
        self.current_moves = self.world.get_moves(self.current_player)
        self.should_continue = True

        if self.next_step_button is not None:
            self.next_step_button.destroy()

        self.next_step_button = Button(self.world.root, text="Start Attacking", command=lambda: self.stop())
        self.next_step_button.pack()

        self.place_troops_iteration()

    def switch_player(self):
        self.current_player = (self.current_player % 2) + 1
        print(f"Player {self.current_player}")

    def play(self):
            self.current_player = 1
            self.place_troops()
            self.world.root.mainloop()




