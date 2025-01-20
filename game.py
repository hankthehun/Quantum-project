import random
from quantum import *
from moves import *
from graph import *

PHASE_TITLES = ["Placing Troops", "Attacking", "Moving Troops"]
PHASE_BUTTONS = ["Start Attacking", "End Attacks", "End Turn"]

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
        self.troop_swap = None
        self.attacking_move = None
        self.defense_iteration = False
        self.selected_basis = None


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
        self.world.canvas.create_text(110, 620, text="Available Gates", font=("Helvetica", 12, "bold"), fill="black", tags="move")
        render_positions = get_move_render_positions(30, 650, len(self.current_moves))
        for i, move in enumerate(self.current_moves):
            x, y = render_positions[i]
            move.render(self.world, x, y, lambda m: self.select_move(m))
        self.world.root.update()

    def render_basis(self):
        self.world.canvas.delete("basis")
        self.world.canvas.create_text(80, 620, text="Measurement Basis", font=("Helvetica", 12, "bold"),
                                      fill="black", tags="basis")

        render_positions = get_move_render_positions(30, 650, len(self.current_moves))

        for i, move in enumerate(self.current_moves):
            x, y = render_positions[i]
            move.render_measurement_basis(self.world, x, y, lambda m=move: self.select_basis(m))

        self.world.root.update()


    def select_basis(self, move):
        if move.selected:
            return
        self.world.allow_selection(True, self.current_player)
        self.selected_move = move
        self.selected_basis = move.basis
        for m in self.current_moves:
            m.set_selected(m == move)
        self.render_basis()


    def select_move(self, move):
        if move.selected:
            return
        self.world.allow_selection(True, self.current_player)
        self.selected_move = move
        for m in self.current_moves:
            m.set_selected(m == move)
        self.render_moves()

    def execute_move(self, move):
        print(move)
        country1 = self.world.get_country(move.country1)
        if not move.is_double_gate():
            self.circuit.apply_single_gate(move.gate, country1.qubits[move.qubit1])
        else:
            country2 = self.world.get_country(move.country2)
            self.circuit.apply_double_gate(move.gate, country2.qubits[move.qubit2], country1.qubits[move.qubit1])

        self.current_moves.remove(move)
        self.selected_move = None
        self.world.allow_selection(False)
        self.world.render()


    def execute_attacking_move(self, attacking_move):
        print(attacking_move)
        attacking_country = self.world.get_country(attacking_move.country1)
        defending_country = self.world.get_country(attacking_move.country2)

        # ACTUAL CODE:
        attacking_country_measurement = self.circuit.measure_in_basis(attacking_country.qubits, self.selected_basis)
        defending_country_measurement = self.circuit.measure_in_basis(defending_country.qubits, self.selected_basis)
        #
        if attacking_country_measurement > defending_country_measurement:
            print(f"Player {self.current_player} won the attack")
            defending_country.owner = self.current_player

        else:
            print(f"Player {self.current_player} lost the attack")
        attacking_country.lost_battle = True




        self.current_moves.clear()
        self.world.selection = ""
        self.selected_move = None
        self.selected_basis = None
        self.attacking_move = None
        self.world.allow_selection(False)
        self.world.render()

        self.attack_phase()


    def execute_troop_swap(self, troop_swap):
        print(troop_swap)
        qubit1 = self.world.get_country(troop_swap.country1).qubits[troop_swap.qubit1]
        qubit2 = self.world.get_country(troop_swap.country2).qubits[troop_swap.qubit2]
        self.circuit.apply_swap(qubit1, qubit2)
        self.world.allow_selection(False)
        self.world.render()


    def execute_later(self, function, time):
        self.world.root.after(time, function)


    def place_troops_iteration(self):
        if len(self.current_moves) <= 0:
            self.should_continue = False

        if self.should_continue:
            self.render_moves()
            if self.world.selection.strip() != "":
                self.ask_for_confirmation()
                if self.confirmed:
                    self.reset_confirmation()

                    if self.selected_move.select_country(self.world.selection):
                        self.execute_move(self.selected_move)
                        self.execute_later(self.place_troops_iteration, 1)
                        return
                    else:
                        if self.selected_move.country1 != "":
                            self.world.allow_selection(True, self.current_player, True)
            self.execute_later(self.place_troops_iteration, 50)
        else:
            self.attack_phase()


    def select_attacking_country_iteration(self):
        self.world.allow_selection(True, self.current_player, False)

        if self.should_continue:
            self.attacking_move.render_selection(self.world)

            if self.world.selection.strip() != "":
                self.ask_for_confirmation()

                if self.confirmed:
                    self.reset_confirmation()

                    if self.attacking_move.select_country(self.world, self.world.selection):
                        self.defense_iteration = True
                        self.select_defending_country_iteration()

            if not self.defense_iteration:
                self.execute_later(self.select_attacking_country_iteration, 50)

        else:
            self.move_troops()


    def select_defending_country_iteration(self):
        self.world.allow_selection(True, self.current_player, True)

        if self.should_continue:
            self.attacking_move.render_selection(self.world)

            if self.world.selection.strip() != "":
                self.ask_for_confirmation()

                if self.confirmed:
                    self.reset_confirmation()

                    if self.attacking_move.select_country(self.world, self.world.selection):
                        self.defense_iteration = False
                        self.select_measuring_basis_iteration()

            if self.defense_iteration:
                self.execute_later(self.select_defending_country_iteration, 50)

        else:
            self.move_troops()


    def select_measuring_basis_iteration(self):
        if self.should_continue:
            self.render_basis()
            self.ask_for_confirmation()

            if self.confirmed:
                self.reset_confirmation()

                if self.confirm_button is None:
                    self.attacking_move.basis = self.selected_basis
                    self.execute_attacking_move(self.attacking_move)
                    return

            self.execute_later(self.select_measuring_basis_iteration, 50)

        else:
            self.move_troops()


    def reset_battles(self):
        for country in self.world.get_all_countries():
            country.lost_battle = False


    def move_troops_iteration(self):
        if self.should_continue:
            self.troop_swap.render(self.world)
            if self.world.selection.strip() != "":
                self.ask_for_confirmation()
                if self.confirmed:
                    self.reset_confirmation()
                    if self.troop_swap.select_country(self.world, self.world.selection):
                        self.execute_troop_swap(self.troop_swap)
                        self.stop()
                        self.execute_later(self.move_troops_iteration, 1)
                        return
            self.execute_later(self.move_troops_iteration, 50)
        else:
            self.world.canvas.delete("swap")
            self.next_step_button.destroy()
            self.next_step_button = None
            self.switch_player()
            self.place_troops()

    def setup_turn_phase(self, phase):
        if phase < 1 or phase > 3:
            return
        self.world.allow_selection(False)
        self.world.selection = ""
        self.world.render()
        self.world.canvas.delete("turn")
        text = f"Phase {phase} : {PHASE_TITLES[phase-1]}"
        self.world.canvas.create_text(self.world.size // 2, 20, text=text, font=("Helvetica", 20),
                                      fill=COLORS[self.current_player], tags="turn")
        self.should_continue = True

        if self.next_step_button is not None:
            self.next_step_button.destroy()

        self.next_step_button = Button(self.world.root, text=PHASE_BUTTONS[phase-1], command=lambda: self.stop())
        self.next_step_button.pack(side=LEFT if self.current_player == 1 else RIGHT)


    def place_troops(self):
        self.setup_turn_phase(1)
        self.current_moves = get_player_placing_moves(self.world, self.current_player)
        self.place_troops_iteration()

    def move_troops(self):
        self.reset_battles()
        self.setup_turn_phase(3)
        self.troop_swap = TroopSwap()
        self.world.allow_selection(True, self.current_player)
        self.world.canvas.delete("attack")
        self.move_troops_iteration()

    def attack_phase(self):
        self.setup_turn_phase(2)
        self.attacking_move = AttackingMove()
        self.current_moves = get_player_attacking_moves()
        self.world.canvas.delete("move")
        self.select_attacking_country_iteration()

    def switch_player(self):
        self.current_player = (self.current_player % 2) + 1

    def play(self):
        self.current_player = 1
        self.place_troops()
        self.world.root.mainloop()




