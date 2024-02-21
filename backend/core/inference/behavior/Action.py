import random

from core.library.BehaviorTreeBase import BehaviorTree, BehaviorTreeNode, BTActionNodeAnnotation
from core.library.EasyImportBase import ROOT


@BTActionNodeAnnotation
class EnemyClosingActionNode(BehaviorTreeNode):

    def __init__(self):
        super().__init__()
        self.__enemy_list = []
        self.__radius = 2.0

    def set_enemy_list(self, enemy_list):
        self.__enemy_list = enemy_list

    def get_enemy_list(self):
        return self.__enemy_list

    def set_radius(self, radius):
        self.__radius = radius

    def get_radius(self):
        return self.__radius

    def should_execute(self):
        return True

    def execute(self, from_to):
        pass


@BTActionNodeAnnotation
class CallingGuardActionNode(BehaviorTreeNode):

    def __init__(self):
        super().__init__()
        self.__minium_value = 30

    def set_minium_value(self, value):
        self.__minium_value = value

    def get_minium_value(self):
        return self.__minium_value

    def should_execute(self):
        return True

    def execute(self, from_to):
        pass


@BTActionNodeAnnotation
class StandByActionNode(BehaviorTreeNode):

    def __init__(self):
        super().__init__()
        self.__silence = False

    def set_silence(self, silence):
        self.__silence = silence

    def get_silence(self):
        return self.__silence

    def should_execute(self):
        return True

    def execute(self, from_to):
        pass


@BTActionNodeAnnotation
class OutpostActionAConditionNode(BehaviorTreeNode):

    def __init__(self):
        super().__init__()
        self.__radius = 10.0
        self.__enable_back_sight = False
        self.__communicate_list = []

    def get_radius(self):
        return self.__radius

    def set_radius(self, radius):
        self.__radius = radius

    def get_enable_back_sight(self):
        return self.__enable_back_sight

    def set_enable_back_sight(self, enable_back_sight):
        self.__enable_back_sight = enable_back_sight

    def get_communicate_list(self):
        return self.communicate_list

    def set_communicate_list(self, communicate_list):
        self.__communicate_list = communicate_list

    def should_execute(self):
        """
        >>> if self.__radius >= 10.0: \
                return False \
            if 'R2' in self.__communicate_list: \
                return True \
            return False
        """
        if self.__radius >= 10.0:
            return False
        if 'R2' in self.__communicate_list:
            return True
        return False

    def execute(self, from_to):
        pass


@BTActionNodeAnnotation
class LookAroundActionNode(BehaviorTreeNode):

    def __init__(self):
        super().__init__()
        self.__radius = 10.0
        self.__enable_back_sight = False
        self.__communicate_list = []

    def get_radius(self):
        return self.__radius

    def set_radius(self, radius):
        self.__radius = radius

    def get_enable_back_sight(self):
        return self.__enable_back_sight

    def set_enable_back_sight(self, enable_back_sight):
        self.__enable_back_sight = enable_back_sight

    def get_communicate_list(self):
        return self.communicate_list

    def set_communicate_list(self, communicate_list):
        self.__communicate_list = communicate_list

    def should_execute(self):
        return True

    def execute(self, from_to):
        pass


@BTActionNodeAnnotation
class WalkingActionNode(BehaviorTreeNode):

    def __init__(self):
        super().__init__()
        self.__speed = 10.0

    def get_speed(self):
        return self.__speed

    def set_speed(self, speed):
        self.__speed = speed

    def should_execute(self):
        return True

    def execute(self, from_to):
        pass


@BTActionNodeAnnotation
class EatActionNode(BehaviorTreeNode):

    def __init__(self):
        super().__init__()
        self.__can_eat_list = []

    def get_can_eat_list(self):
        return self.__can_eat_list

    def set_can_eat_list(self, can_eat_list):
        self.__can_eat_list = can_eat_list

    def should_execute(self):
        return True

    def execute(self, from_to):
        pass


@BTActionNodeAnnotation
class SwimActionNode(BehaviorTreeNode):

    def __init__(self):
        super().__init__()
        self.__speed = 10.0

    def get_speed(self):
        return self.__speed

    def set_speed(self, speed):
        self.__speed = speed

    def should_execute(self):
        return True

    def execute(self, from_to):
        pass


@BTActionNodeAnnotation
class OpenDoorActionNode(BehaviorTreeNode):

    def __init__(self):
        super().__init__()

    def should_execute(self):
        return True

    def execute(self, from_to):
        pass


# Created by Simulate Ground
@BTActionNodeAnnotation
class SwimmingActionNode(BehaviorTreeNode):

    def __init__(self):
        super().__init__()
        self.__in_water = False
        self.__in_lava = False

    def set_in_water(self, in_water):
        self.__in_water = in_water

    def get_in_water(self):
        return self.__in_water

    def set_in_lava(self, in_lava):
        self.__in_lava = in_lava

    def get_in_lava(self):
        return self.__in_lava

    def execute(self, from_to):
        if self.should_execute():
            self.logger.info("Entity is swimming now.")

    def should_execute(self):
        return self.__in_lava or self.__in_water


@BTActionNodeAnnotation
class AttackMeleeActionNode(BehaviorTreeNode):

    def __init__(self):
        super().__init__()
        self.__speed = 1.0
        self.__use_long_memory = False

    def set_speed(self, speed):
        self.__speed = speed

    def get_speed(self):
        return self.__speed

    def set_use_long_memory(self, u):
        self.__use_long_memory = u

    def get_use_long_memory(self):
        return self.__use_long_memory

    def execute(self, from_to):
        self.logger("Entity meet the attack.")

    def should_execute(self):
        return True


@BTActionNodeAnnotation
class TakeBlockActionNode(BehaviorTreeNode):

    def __init__(self):
        super().__init__()
        self.__block_list = []

    def set_block_list(self, block_list):
        self.__block_list = block_list

    def get_block_list(self):
        return self.__block_list

    def execute(self, from_to):
        if self.should_execute():
            self.logger("Entity pick up the block.")

    def should_execute(self):
        block = random.randint(0, len(self.__block_list))
        if block in self.__block_list[:len(self.__block_list) // 2]:
            return True
        return False


@BTActionNodeAnnotation
class PlaceBlockActionNode(BehaviorTreeNode):

    def __init__(self):
        super().__init__()
        self.__duration = 0

    def execute(self, from_to):
        if self.should_execute():
            self.logger("Entity place the block.")

    def should_execute(self):
        if self.__duration >= 1000:
            return True
        self.__duration += 1
        return False


bt = BehaviorTree()
bt.build_bt_from_config_file(ROOT('behavior_tree_config/config.json'))
bt.start(1)
