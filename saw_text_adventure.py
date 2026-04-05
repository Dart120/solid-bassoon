"""Saw-themed text adventure game.

This module implements a command-line text adventure inspired by the
"Saw" film series. Players must explore, inspect, and interact with their
environment to solve puzzles and ultimately escape.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from textwrap import dedent
from typing import Dict, Iterable, List, Optional, Tuple


def wrap(text: str) -> str:
    """Return a neatly formatted text block.

    The adventure descriptions contain many multi-line strings. Wrapping
    them through :func:`textwrap.dedent` keeps indentation tidy while still
    allowing the script to display clean paragraphs when printed.
    """

    return dedent(text).strip()


@dataclass
class Player:
    """State container representing the player's condition."""

    inventory: Dict[str, str] = field(default_factory=dict)
    morality: int = 0
    alive: bool = True

    def has_item(self, name: str) -> bool:
        return name in self.inventory


class Game:
    """Main controller for the Saw-themed text adventure."""

    START_ROOM = "bathroom"
    DOOR_CODE = "613"

    def __init__(self) -> None:
        self.player = Player()
        self.current_room = self.START_ROOM
        self.running = True

        # Flags that control environmental state and narrative beats.
        self.flags: Dict[str, bool] = {
            "hacksaw_available": False,
            "uv_light_available": False,
            "tape_available": False,
            "note_available": False,
            "key_available": False,
            "fuse_available": False,
            "chain_unlocked": False,
            "x_revealed": False,
            "saw_broken": False,
            "door_keypad_unlocked": False,
            "bathroom_door_open": False,
            "tape_played": False,
            "note_read": False,
            "generator_powered": False,
            "syringe_available": True,
            "prisoner_sedated": False,
            "prisoner_helped": False,
        }

        # Cache of known interactive targets. Parsing the "use" command
        # relies on this set to interpret multi-word item names.
        self.known_targets: Dict[str, Iterable[str]] = {
            "bathroom": (
                "chain",
                "door",
                "door_keypad",
                "tub",
                "corpse",
                "walls",
                "clock",
                "x",
                "lockbox",
            ),
            "hallway": (
                "generator",
                "door",
                "exit",
                "panel",
                "prisoner",
                "cage",
                "table",
            ),
        }

        self.intro_shown = False

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    @staticmethod
    def normalize(text: str) -> str:
        """Normalize player input to a consistent token."""

        return "_".join(text.strip().lower().split())

    def known_items(self) -> Iterable[str]:
        """Return a list of items the parser should recognise."""

        items = {
            "hacksaw",
            "uv_light",
            "tape_recorder",
            "note",
            "shackle_key",
            "fuse",
            "syringe",
            "keypad",
            "chain",
            "door",
            "generator",
            "prisoner",
            "cage",
            "panel",
            "exit",
        }
        items.update(self.player.inventory.keys())
        return items

    # ------------------------------------------------------------------
    # Game loop
    # ------------------------------------------------------------------
    def play(self) -> None:
        """Start the adventure loop."""

        print(self.intro_text())
        print(self.describe_current_room())

        while self.running and self.player.alive:
            raw_command = input("\n> ").strip()
            if not raw_command:
                continue
            response = self.process_command(raw_command)
            if response:
                print(response)

    # ------------------------------------------------------------------
    # Descriptions
    # ------------------------------------------------------------------
    def intro_text(self) -> str:
        """Narrative introduction for the adventure."""

        if self.intro_shown:
            return ""
        self.intro_shown = True
        return wrap(
            """
            You wake in a lightless, fetid bathroom. Cold water pools around
            you as a metal shackle bites into your ankle. Across the tiled
            floor a decaying corpse lies face down in a crimson puddle, one
            hand still gripping a small recorder. The door is secured by a
            keypad lock, and somewhere in the darkness a mechanised voice
            crackles to life.
            """
        )

    def describe_current_room(self) -> str:
        """Return a description of the player's current location."""

        if self.current_room == "bathroom":
            return self.describe_bathroom()
        if self.current_room == "hallway":
            return self.describe_hallway()
        return "You are lost in darkness."

    def describe_bathroom(self) -> str:
        parts: List[str] = [
            "The bathroom is a ruin of cracked tiles and flickering light.",
        ]
        if not self.flags["chain_unlocked"]:
            parts.append("A heavy shackle keeps you anchored to a rusted pipe.")
        else:
            parts.append("The broken shackle dangles loosely from the pipe.")

        if not self.flags["bathroom_door_open"]:
            parts.append(
                "A reinforced door with a grime-coated keypad blocks the only exit."
            )
        else:
            parts.append("The bathroom door hangs ajar, revealing a shadowed hallway.")

        if not self.flags["hacksaw_available"] and "hacksaw" not in self.player.inventory:
            parts.append("An old bathtub squats nearby, its murky water hiding shapes.")
        if not self.flags["tape_available"] and "tape_recorder" not in self.player.inventory:
            parts.append("The corpse clutches something small and metallic in its hand.")

        return " ".join(parts)

    def describe_hallway(self) -> str:
        parts = [
            "A narrow industrial hallway stretches ahead, stinking of rust and ozone.",
            "Thick cables run to a humming generator beside a barred cage where a terrified prisoner waits.",
            "At the far end, an exit door glows with a red biometric scanner.",
        ]
        if not self.flags["generator_powered"]:
            parts.append("The generator is dark; the scanner pulses impatiently.")
        else:
            parts.append("Power surges through the walls as the scanner shifts to a hopeful green.")
        if self.flags["syringe_available"] and "syringe" not in self.player.inventory:
            parts.append("A metal tray holds a labeled syringe within arm's reach.")
        return " ".join(parts)

    # ------------------------------------------------------------------
    # Command processing
    # ------------------------------------------------------------------
    def process_command(self, raw_command: str) -> str:
        command = raw_command.strip()
        verb, *rest = command.split(maxsplit=1)
        verb = verb.lower()
        target = rest[0] if rest else ""

        if verb in {"quit", "exit"}:
            self.running = False
            return "You let the darkness take you. Game over."
        if verb == "help":
            return self.help_text()
        if verb == "look":
            return self.describe_current_room()
        if verb == "inventory":
            return self.show_inventory()
        if verb == "status":
            return self.show_status()
        if verb == "inspect":
            return self.inspect(target)
        if verb == "take":
            return self.take(target)
        if verb == "use":
            return self.use(target)
        if verb == "move":
            return self.move(target)
        if verb == "talk":
            return self.talk(target)
        if verb == "release":
            return self.release(target)

        return "The silence offers no response to that action."

    # ------------------------------------------------------------------
    # Command helpers
    # ------------------------------------------------------------------
    def help_text(self) -> str:
        return wrap(
            """
            Available commands:
              look                        — Re-describe the current room.
              inspect <object>            — Examine something more closely.
              take <item>                — Pick up an item.
              use <item> [on <target>]   — Use an item, optionally on a target.
              move <location>            — Attempt to move to a new area.
              talk <target>              — Speak to another captive.
              release <target>           — Attempt to release someone or something.
              inventory                  — View held items.
              status                     — View your condition.
              help                       — Display this help text.
              quit                       — Give up.

            Commands are not case sensitive. Multi-word items such as "uv light"
            can be entered with or without a space ("uv light" or "uv_light").
            """
        )

    def show_inventory(self) -> str:
        if not self.player.inventory:
            return "Your hands are empty; every breath tastes of desperation."
        parts = ["You clutch the following items:"]
        for item, description in self.player.inventory.items():
            parts.append(f"  - {item.replace('_', ' ')}: {description}")
        return "\n".join(parts)

    def show_status(self) -> str:
        chain_status = "broken" if self.flags["chain_unlocked"] else "locked"
        morality = self.player.morality
        return wrap(
            f"""
            Shackled ankle: {chain_status}
            Morality score: {morality} (higher indicates compassion)
            """
        )

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------
    def parse_object(self, raw: str) -> str:
        return self.normalize(raw)

    def parse_use_arguments(self, raw: str) -> Tuple[str, str]:
        raw = raw.strip()
        if not raw:
            return "", ""
        tokens = raw.split()

        prepositions = {"on", "with", "to", "at", "into", "in", "against"}
        for index, token in enumerate(tokens):
            if token.lower() in prepositions:
                item_tokens = tokens[:index]
                target_tokens = tokens[index + 1 :]
                item = self.normalize(" ".join(item_tokens))
                target = self.normalize(" ".join(target_tokens))
                return item, target

        # Attempt to match the longest possible item name.
        for length in range(len(tokens), 0, -1):
            candidate = self.normalize(" ".join(tokens[:length]))
            if candidate in self.known_items():
                remainder = tokens[length:]
                item = candidate
                target = self.normalize(" ".join(remainder))
                return item, target

        # Fallback: treat the first word as the item.
        item = self.normalize(tokens[0])
        target = self.normalize(" ".join(tokens[1:]))
        return item, target

    # ------------------------------------------------------------------
    # Inspect interactions
    # ------------------------------------------------------------------
    def inspect(self, raw_target: str) -> str:
        if not raw_target:
            return "Inspect what?"

        target = self.parse_object(raw_target)

        if self.current_room == "bathroom":
            return self.inspect_bathroom(target)
        if self.current_room == "hallway":
            return self.inspect_hallway(target)
        return "There is nothing of interest."

    def inspect_bathroom(self, target: str) -> str:
        if target == "chain":
            if self.flags["chain_unlocked"]:
                return "The shackle lies open, its teeth dull with blood."
            return wrap(
                """
                The shackle is thick and polished from struggle. A heavy padlock
                keeps it sealed around your ankle. You'll need a key—or
                something drastic—to remove it.
                """
            )
        if target in {"tub", "bathtub"}:
            if not self.flags["hacksaw_available"] and "hacksaw" not in self.player.inventory:
                self.flags["hacksaw_available"] = True
                self.flags["uv_light_available"] = True
                return wrap(
                    """
                    You plunge your hands into the cold water. Your fingers brush
                    against a bundled cloth containing a rusted hacksaw and a
                    small ultraviolet penlight. Both could become vital.
                    """
                )
            return "Only stagnant water and broken tiles remain."
        if target == "corpse":
            message = [
                "The corpse's skin is ashen, the jaw slack.",
            ]
            if not self.flags["tape_available"] and "tape_recorder" not in self.player.inventory:
                self.flags["tape_available"] = True
                message.append(
                    "You prise a battered tape recorder from its fingers. A blood-specked note is tucked inside the shirt pocket."
                )
                self.flags["note_available"] = True
            else:
                message.append("You already searched the body; nothing else remains.")
            return " ".join(message)
        if target == "walls":
            if self.flags["x_revealed"]:
                return "A faint UV-painted X glows on the tiles near the door."
            return wrap(
                """
                Filthy tiles cover the walls from floor to ceiling. Scratches
                and dried blood form meaningless patterns in the dim light.
                Perhaps another type of light would reveal more.
                """
            )
        if target == "clock":
            self.flags["note_read"] = True
            return wrap(
                """
                A cracked wall clock hangs frozen. Its hour hand lies between six
                and seven, the minute hand fixed on thirteen minutes past. Dusty
                red fingerprints smear the glass at those numbers.
                """
            )
        if target == "door":
            if self.flags["bathroom_door_open"]:
                return "The door is ajar, granting a narrow path into the hallway."
            return wrap(
                """
                The reinforced door boasts a metal keypad and no visible handle.
                Three digits will unlock it, according to the etched warning:
                "Time remembers what you try to forget."
                """
            )
        if target in {"keypad", "door_keypad"}:
            return "Three grimy buttons await the correct sequence."
        if target == "x":
            if not self.flags["x_revealed"]:
                return "You see nothing noteworthy."
            if not self.flags["key_available"]:
                self.flags["key_available"] = True
                self.flags["fuse_available"] = True
                return wrap(
                    """
                    Behind the glowing X, a loose tile conceals a hidden cavity.
                    Inside lies a brass key attached to a numbered tag and a small
                    electrical fuse bundled in wax paper.
                    """
                )
            return "The cavity behind the tile is empty now."
        if target == "lockbox":
            if not self.flags["x_revealed"]:
                return "No lockbox is visible here."
            if self.flags["key_available"]:
                return "The lockbox held the key and fuse; nothing else rests inside."
            return "Only dust coats the metal container."
        if target == "note":
            if "note" in self.player.inventory:
                return self.read_note()
            if self.flags["note_available"]:
                return wrap(
                    """
                    A blood-specked note dangles from the corpse's pocket,
                    waiting to be taken.
                    """
                )
            return "You see no note to inspect."
        if target == "tape_recorder":
            if "tape_recorder" in self.player.inventory:
                return wrap(
                    """
                    The recorder is scuffed but functional. A small label reads,
                    "Play me."
                    """
                )
            if self.flags["tape_available"]:
                return "The recorder lies beside the corpse, begging to be taken."
            return "You cannot see that item."
        if target in {"hacksaw", "uv_light", "shackle_key", "fuse"}:
            if target in self.player.inventory:
                return self.player.inventory[target]
            availability_flag = f"{target}_available"
            if availability_flag in self.flags and self.flags[availability_flag]:
                return "It rests within reach, waiting to be taken."
            return "You do not spot that here."

        return "There is nothing noteworthy about that."

    def inspect_hallway(self, target: str) -> str:
        if target in {"generator", "panel"}:
            if self.flags["generator_powered"]:
                return wrap(
                    """
                    The generator thrums steadily, indicator lights glowing green.
                    The adjacent control panel now displays "POWER ROUTED".
                    """
                )
            return wrap(
                """
                The generator sits idle, its panel flashing "FUSE MISSING".
                Thick cables run toward the exit door's scanner.
                """
            )
        if target in {"door", "exit"}:
            if not self.flags["generator_powered"]:
                return wrap(
                    """
                    A steel door guards the exit, locked by a biometric scanner
                    that draws no power. Without electricity it will never open.
                    """
                )
            return wrap(
                """
                The exit door hums with power. A sign reads, "One life for
                another." A palm-shaped sensor glows, waiting.
                """
            )
        if target in {"prisoner", "cage"}:
            if self.flags["prisoner_helped"]:
                return "The cage stands open, its occupant gone with a whispered thank you."
            if self.flags["prisoner_sedated"]:
                return wrap(
                    """
                    The prisoner slumps peacefully, the shotgun collar still
                    locked around their neck. They breathe in shallow, sedated gasps.
                    """
                )
            return wrap(
                """
                A gaunt prisoner trembles inside the cage, a shotgun collar
                poised beneath their jaw. A lever outside the bars promises
                release—or death—depending on how the trap was primed.
                """
            )
        if target == "table":
            if self.flags["syringe_available"] and "syringe" not in self.player.inventory:
                return wrap(
                    """
                    The metal tray holds a syringe labeled "Midazolam" along with
                    instructions: "Sedate before release. Mercy is a choice."
                    """
                )
            return "Only empty trays and instruments lie here."
        if target == "syringe":
            if "syringe" in self.player.inventory:
                return self.player.inventory["syringe"]
            if self.flags["syringe_available"]:
                return "The syringe waits on the tray, capped and ready."
            return "You cannot see that here."

        return "The shadows conceal nothing more of interest."

    # ------------------------------------------------------------------
    # Take interactions
    # ------------------------------------------------------------------
    def take(self, raw_target: str) -> str:
        if not raw_target:
            return "Take what?"

        item = self.parse_object(raw_target)

        if self.current_room == "bathroom":
            return self.take_bathroom(item)
        if self.current_room == "hallway":
            return self.take_hallway(item)
        return "You grasp at empty air."

    def take_bathroom(self, item: str) -> str:
        if item == "hacksaw" and self.flags["hacksaw_available"]:
            self.flags["hacksaw_available"] = False
            self.player.inventory["hacksaw"] = "A rusted hacksaw with a fragile blade."
            return "You take the hacksaw. Its blade looks worryingly brittle."
        if item == "uv_light" and self.flags["uv_light_available"]:
            self.flags["uv_light_available"] = False
            self.player.inventory["uv_light"] = "A pen-sized ultraviolet light."
            return "You pocket the ultraviolet penlight."
        if item == "tape_recorder" and self.flags["tape_available"]:
            self.flags["tape_available"] = False
            self.player.inventory["tape_recorder"] = "A battered recorder labeled 'Play me.'"
            return "You take the tape recorder; it crackles softly."
        if item == "note" and self.flags["note_available"]:
            self.flags["note_available"] = False
            self.player.inventory["note"] = "A blood-specked note from the corpse."
            return "You take the folded note; dried blood stains your fingers."
        if item == "shackle_key" and self.flags["key_available"]:
            self.flags["key_available"] = False
            self.player.inventory["shackle_key"] = "A brass key tagged 'Shackle'."
            return "You retrieve the brass key from the hidden cavity."
        if item == "fuse" and self.flags["fuse_available"]:
            self.flags["fuse_available"] = False
            self.player.inventory["fuse"] = "A pristine electrical fuse wrapped in wax paper."
            return "You take the fuse, its glass cylinder surprisingly intact."

        return "Your fingers close on nothing useful."

    def take_hallway(self, item: str) -> str:
        if item == "syringe" and self.flags["syringe_available"]:
            self.flags["syringe_available"] = False
            self.player.inventory["syringe"] = "A syringe of fast-acting sedative."
            return "You pocket the syringe, its label warning of deep sleep."
        return "You can't take that."

    # ------------------------------------------------------------------
    # Use interactions
    # ------------------------------------------------------------------
    def use(self, raw_target: str) -> str:
        item_name, target_name = self.parse_use_arguments(raw_target)
        if not item_name:
            return "Use what?"

        if self.current_room == "bathroom":
            return self.use_bathroom(item_name, target_name)
        if self.current_room == "hallway":
            return self.use_hallway(item_name, target_name)
        return "Nothing happens."

    def use_bathroom(self, item: str, target: str) -> str:
        if item == "tape_recorder":
            if "tape_recorder" not in self.player.inventory:
                return "You need to pick up the recorder first."
            if self.flags["tape_played"]:
                return "The recorder's message has already seared into your mind."
            self.flags["tape_played"] = True
            return wrap(
                """
                The recorder crackles: "Hello survivor. You spent years hiding
                from the moment your son vanished—June 13th, 6:13 p.m. Time
                remembers, even when you refuse. The key to your chain lies in
                the dark. Only light beyond sight reveals it. Live or die. Make
                your choice."
                """
            )

        if item == "note":
            if "note" not in self.player.inventory:
                return "The note rests just out of reach; you must take it first."
            return self.read_note()

        if item == "uv_light":
            if "uv_light" not in self.player.inventory:
                return "You fumble for a light you don't possess."
            if target in {"walls", "door", "tiles"}:
                if self.flags["x_revealed"]:
                    return "The ultraviolet glow once again highlights the X on the tiles."
                self.flags["x_revealed"] = True
                return wrap(
                    """
                    You sweep the ultraviolet light across the wall. Invisible
                    paint flares to life, revealing a stark X near the door.
                    Something hides behind those tiles.
                    """
                )
            return "The feeble beam reveals nothing useful there."

        if item == "hacksaw":
            if "hacksaw" not in self.player.inventory:
                return "You no longer have the hacksaw."
            if self.flags["saw_broken"]:
                return "The hacksaw's snapped blade can't cut anything now."
            if target in {"chain", "shackle"}:
                self.flags["saw_broken"] = True
                self.player.inventory.pop("hacksaw")
                return wrap(
                    """
                    You saw furiously at the chain. Sparks fly, but the brittle
                    blade snaps uselessly. You are left with a mangled handle."
                    """
                )
            if target in {"foot", "leg", "self"}:
                self.player.alive = False
                self.running = False
                return wrap(
                    """
                    In desperation you turn the blade on yourself. Agony surges
                    through your body before darkness swallows you. The game
                    ends here.
                    """
                )
            return "You brandish the hacksaw aimlessly with no effect."

        if item in {"shackle_key", "key"}:
            if "shackle_key" not in self.player.inventory:
                return "You must find a key first."
            if target in {"chain", "shackle", "lock"}:
                if self.flags["chain_unlocked"]:
                    return "The shackle already hangs open."
                self.flags["chain_unlocked"] = True
                return wrap(
                    """
                    The key clicks in the padlock. With trembling hands you free
                    your ankle. Blood returns to your numb foot.
                    """
                )
            return "The key doesn't fit anything else here."

        if item in {"keypad", "door", "door_keypad"}:
            if target == "":
                return (
                    "Enter which code?"
                    if not self.flags["door_keypad_unlocked"]
                    else "The keypad already accepted the code."
                )
            code = target.replace("_", "")
            if code == self.DOOR_CODE:
                if not self.flags["chain_unlocked"]:
                    return wrap(
                        """
                        The keypad beeps in acceptance, but the chain at your ankle
                        yanks you back. Free yourself before trying to leave.
                        """
                    )
                if self.flags["bathroom_door_open"]:
                    return "The door remains unlocked; the keypad displays a green light."
                self.flags["door_keypad_unlocked"] = True
                self.flags["bathroom_door_open"] = True
                return wrap(
                    """
                    The keypad emits a cheerful chime as the lock releases. The
                    door cracks open, exhaling the stench of stale air from the
                    hallway beyond.
                    """
                )
            return "The keypad flashes red—wrong code."

        if item == "door" and target in {"", "open"}:
            if self.flags["bathroom_door_open"]:
                return "You've already opened the door."
            return "The keypad holds it firmly shut."

        return "That accomplishes nothing."

    def use_hallway(self, item: str, target: str) -> str:
        if item == "fuse":
            if "fuse" not in self.player.inventory:
                return "You left the fuse behind."
            if target not in {"generator", "panel"}:
                return "The fuse won't fit there."
            if self.flags["generator_powered"]:
                return "The generator already hums with power."
            self.flags["generator_powered"] = True
            self.player.inventory.pop("fuse")
            return wrap(
                """
                You slot the fuse into place. The generator roars to life, lights
                blazing down the hallway as the exit scanner glows green.
                """
            )

        if item == "syringe":
            if "syringe" not in self.player.inventory:
                return "You must take the syringe first."
            if target not in {"prisoner", "captive"}:
                return "That's not a wise target for the sedative."
            if self.flags["prisoner_helped"]:
                return "The prisoner is already free."
            if self.flags["prisoner_sedated"]:
                return "The prisoner already slumps in a drugged haze."
            self.flags["prisoner_sedated"] = True
            return wrap(
                """
                You inject the sedative through a gap in the bars. The prisoner's
                frantic breathing slows as the drug takes hold, their eyes
                pleading with you even as consciousness fades.
                """
            )

        if item in {"door", "exit"}:
            if not self.flags["generator_powered"]:
                return "The exit refuses to budge without power."
            return self.trigger_finale(force=True)

        if item == "generator":
            if self.flags["generator_powered"]:
                return "You adjust a few knobs; the power output remains steady."
            return "Without a fuse, the controls do nothing."

        if item == "panel" and target == "door":
            if not self.flags["generator_powered"]:
                return "The panel is lifeless until the generator runs."
            return "The panel routes power directly to the exit scanner."

        return "Nothing meaningful happens."

    # ------------------------------------------------------------------
    # Movement and interactions
    # ------------------------------------------------------------------
    def move(self, raw_target: str) -> str:
        if not raw_target:
            return "Move where?"

        destination = self.parse_object(raw_target)

        if self.current_room == "bathroom":
            if destination in {"door", "hallway", "exit"}:
                if not self.flags["chain_unlocked"]:
                    return "The shackle drags you back; free yourself first."
                if not self.flags["bathroom_door_open"]:
                    return "The door remains locked tight."
                self.current_room = "hallway"
                return self.describe_current_room()
            return "You have nowhere else to go within these four walls."

        if self.current_room == "hallway":
            if destination in {"bathroom"}:
                self.current_room = "bathroom"
                return self.describe_current_room()
            if destination in {"door", "exit"}:
                if not self.flags["generator_powered"]:
                    return "The exit remains sealed until power is restored."
                return self.trigger_finale()
            return "The hallway offers only forward and back."

        return "You cannot move that way."

    def talk(self, raw_target: str) -> str:
        if not raw_target:
            return "Talk to whom?"
        target = self.parse_object(raw_target)

        if self.current_room == "bathroom":
            if target == "corpse":
                return "The corpse answers only with silence."
            return "No one else is here to listen."

        if self.current_room == "hallway":
            if target == "prisoner":
                if self.flags["prisoner_helped"]:
                    return "Their grateful farewell echoes faintly in your ears."
                if self.flags["prisoner_sedated"]:
                    return "The sedated prisoner mumbles incoherently."
                return wrap(
                    """
                    "Please," the prisoner begs, "I don't know why I'm here.
                    The lever outside says it will free me if the collar is safe.
                    I can help you if I survive."
                    """
                )
            return "Your voice dies in the empty hall."

        return "You speak into the void."

    def release(self, raw_target: str) -> str:
        if not raw_target:
            return "Release what?"
        target = self.parse_object(raw_target)

        if self.current_room != "hallway" or target not in {"prisoner", "cage"}:
            return "There is nothing here that you can release."

        if self.flags["prisoner_helped"]:
            return "The cage already stands open."

        if not self.flags["generator_powered"]:
            return wrap(
                """
                You tug the lever but an indicator flashes red: "POWER REQUIRED".
                The release mechanism needs electricity.
                """
            )

        if not self.flags["prisoner_sedated"]:
            self.player.alive = False
            self.running = False
            return wrap(
                """
                You pull the lever. The collar detonates in a thunderous boom,
                shredding the prisoner and peppering you with shrapnel. The last
                thing you hear is Jigsaw's disappointed sigh.
                """
            )

        self.flags["prisoner_helped"] = True
        self.player.morality += 1
        return wrap(
            """
            You pull the lever. With the generator humming, the collar clicks
            harmlessly open. The groggy prisoner stumbles free, whispering,
            "Thank you... I'll trigger the door when you're ready."
            """
        )

    # ------------------------------------------------------------------
    # Narrative helpers
    # ------------------------------------------------------------------
    def read_note(self) -> str:
        self.flags["note_read"] = True
        return wrap(
            """
            The note reads: "The night your boy vanished you stared at the clock
            as 6:13 etched itself into your soul. Time holds you captive. Let it
            guide you now."
            """
        )

    def trigger_finale(self, force: bool = False) -> str:
        if not force:
            if self.flags["prisoner_helped"]:
                ending = self.good_ending()
            else:
                ending = self.neutral_ending()
        else:
            if not self.flags["prisoner_helped"]:
                ending = self.neutral_ending()
            else:
                ending = self.good_ending()
        self.running = False
        return ending

    def good_ending(self) -> str:
        return wrap(
            """
            Together you and the freed prisoner place your hands on the scanner.
            The door slams open. Sirens wail in the distance. Behind you, a
            hidden speaker crackles: "Compassion is the only cure for apathy."
            You helped another survive, and in doing so reclaimed a fragment of
            your humanity. The game is over—for now.
            """
        )

    def neutral_ending(self) -> str:
        return wrap(
            """
            You place your hand on the scanner. The door releases with a hiss,
            abandoning the prisoner to their fate. As you flee, a final message
            rasps from the walls: "You live, but what of the choices you made?"
            Freedom tastes bitter. The game is over—but the consequences remain.
            """
        )


def main() -> None:
    """Entry point for running the adventure as a script."""

    Game().play()


if __name__ == "__main__":
    main()
