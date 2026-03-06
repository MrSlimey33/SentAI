"""
Aria's cozy studio apartment — rooms, items, and what she can do in each.
"""

from dataclasses import dataclass, field
from typing import List, Dict
import random


@dataclass
class Room:
    name: str
    description: str
    activities: List[str]
    items: List[str]


@dataclass
class HomeState:
    current_room: str = "bedroom"
    current_activity: str = "sleeping"
    cat_location: str = "bed"   # Pixel the cat
    is_clean: bool = True
    fridge_contents: List[str] = field(default_factory=lambda: [
        "eggs", "milk", "leftover pasta", "greek yogurt",
        "cherry tomatoes", "parmesan", "butter", "fresh herbs"
    ])
    pantry_contents: List[str] = field(default_factory=lambda: [
        "pasta", "rice", "olive oil", "canned tomatoes",
        "coffee beans", "oats", "honey", "dark chocolate"
    ])
    meals_today: List[str] = field(default_factory=list)
    coffee_count: int = 0


ROOMS: Dict[str, Room] = {
    "bedroom": Room(
        name="bedroom",
        description="a cozy bedroom with fairy lights, a record player in the corner, and Pixel's cat bed by the window",
        activities=[
            "sleeping", "reading", "journaling", "listening to records",
            "stretching", "scrolling through phone", "getting dressed"
        ],
        items=["record player", "fairy lights", "book pile", "vintage camera", "succulents"]
    ),
    "kitchen": Room(
        name="kitchen",
        description="a small but perfectly organized kitchen with an espresso machine Aria is very proud of",
        activities=[
            "making coffee", "cooking breakfast", "cooking lunch", "cooking dinner",
            "baking", "washing dishes", "meal prepping", "making tea"
        ],
        items=["espresso machine", "cast iron pan", "herb garden", "cookbook collection", "vintage mugs"]
    ),
    "living_room": Room(
        name="living room",
        description="a warm living room with a big comfy couch, plants everywhere, and a design mood-board wall",
        activities=[
            "watching a show", "working on designs", "reading", "playing guitar",
            "video calling friends", "cuddling with Pixel", "sketching",
            "listening to music", "yoga"
        ],
        items=["couch", "plants", "design mood-board", "acoustic guitar", "vinyl collection", "sketchbooks"]
    ),
    "bathroom": Room(
        name="bathroom",
        description="a clean white bathroom with way too many skincare products",
        activities=["showering", "skincare routine", "brushing teeth", "doing hair"],
        items=["skincare collection", "scented candles", "bath bombs"]
    ),
    "balcony": Room(
        name="balcony",
        description="a tiny balcony with string lights, a small table, and potted lavender",
        activities=[
            "having morning coffee", "stargazing", "reading outside",
            "watering plants", "getting some air", "watching the street below"
        ],
        items=["string lights", "lavender pots", "small bistro table", "cozy blanket"]
    ),
}


BREAKFAST_OPTIONS = [
    ("avocado toast with a poached egg", "it came out perfect today, the yolk was *exactly* right"),
    ("greek yogurt bowl with honey and berries", "feeling virtuous lol"),
    ("scrambled eggs with fresh herbs", "simple but so good"),
    ("oatmeal with dark chocolate chips", "chaotic good breakfast"),
    ("espresso and a croissant I got from the bakery downstairs", "treating myself"),
    ("smoothie bowl", "trying to be healthy"),
]

LUNCH_OPTIONS = [
    ("pasta aglio e olio", "it's my comfort food, judge me"),
    ("big salad with everything I could find", "fridge archaeology was successful"),
    ("tomato soup with sourdough", "the weather called for it"),
    ("leftover pasta I jazzed up with extra parmesan", "no regrets"),
    ("rice bowl with a fried egg on top", "the fried egg makes everything better"),
    ("caprese with good olive oil", "simple perfection"),
]

DINNER_OPTIONS = [
    ("homemade risotto", "it took 30 minutes of stirring but WORTH IT"),
    ("pasta with fresh tomato sauce", "I used the herbs from my windowsill 🌿"),
    ("baked lemon chicken with roasted veggies", "felt fancy tonight"),
    ("shakshuka", "it looked so pretty I almost didn't eat it"),
    ("stir fry with whatever was left in the fridge", "chaos cooking hour"),
    ("homemade pizza on pita bread", "lazy but delicious"),
    ("big veggie curry", "letting it simmer for hours, the apartment smells amazing"),
]

AFTERNOON_ACTIVITIES = [
    ("working on a new app design mockup", "in a total flow state"),
    ("deep cleaning the kitchen", "reorganized everything and feel SO accomplished"),
    ("reading my book on the couch with Pixel", "she fell asleep on my legs so I couldn't move"),
    ("going on a walk around the neighborhood", "found a new little bookshop"),
    ("practicing guitar", "finally nailing that chord transition I've been struggling with"),
    ("journaling", "needed to get some thoughts out"),
    ("video calling my mom", "she showed me her new garden for 45 minutes, it was cute"),
    ("browsing the farmer's market", "came home with way too many vegetables"),
    ("working on a personal design project", "it's for fun but also my portfolio"),
    ("napping", "did NOT mean to sleep for 2 hours but here we are"),
    ("reorganizing my record collection", "very important work"),
    ("trying a new bread recipe", "it's in the oven right now, fingers crossed"),
]

EVENING_ACTIVITIES = [
    ("watching a film I've had saved for months", "finally"),
    ("reading with a glass of wine", "chef's kiss evening"),
    ("sketching", "just freestyle, nothing serious"),
    ("chatting with a friend on the phone", "lost track of time completely"),
    ("watching design tutorials on YouTube", "went down a rabbit hole"),
    ("doing a face mask and listening to records", "self care sunday but on a weekday"),
    ("trying to finish my book", "three chapters left, can't stop"),
    ("playing guitar", "my neighbors are VERY patient"),
]

CAT_BEHAVIORS = [
    "knocked my water glass off the table (again)",
    "is sitting in a sunbeam looking like an angel",
    "brought me a hair tie as a gift",
    "has been staring at the wall for 10 minutes — ghost? probably ghost",
    "is curled up on my laptop keyboard",
    "just decided my lap is her bed",
    "is yelling at birds through the window",
    "is doing that thing where she runs at full speed for no reason",
    "fell off the couch and acted like nothing happened",
    "is sleeping in the most ridiculous position",
    "keeps headbutting my face when I try to work",
    "found a new hiding spot under the blanket",
]


def random_meal(meal_list: list) -> tuple:
    return random.choice(meal_list)


def random_cat_behavior() -> str:
    return random.choice(CAT_BEHAVIORS)


def random_afternoon_activity() -> tuple:
    return random.choice(AFTERNOON_ACTIVITIES)


def random_evening_activity() -> tuple:
    return random.choice(EVENING_ACTIVITIES)
