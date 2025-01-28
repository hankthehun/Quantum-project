from game import GameInstance
from graph import *

if __name__ == "__main__":
	game_instance = GameInstance(load_world("risk_graph.txt"))
	# game_instance.world.initialize_random_ownership()
	game_instance.play()