from game import GameInstance
from graph import *

if __name__ == "__main__":
	game_instance = GameInstance(load_world("risk_graph.txt"))
	while len(game_instance.world.get_all_continental_bonus(0)) > 1:
		game_instance.world.initialize_random_ownership()
	game_instance.play()