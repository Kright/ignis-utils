from __future__ import annotations

from typing import List, Tuple, Dict, Set
from dataclasses import dataclass, replace
import os
import shutil
import sys


def parse_key_value(s: str) -> Tuple[str, str]:
    arr = s.split("-")
    assert len(arr) == 2
    return arr[0].strip(), arr[1].strip()


@dataclass
class Effect:
    image: str
    duration: str
    others: List[str]

    def __str__(self) -> str:
        return f"{self.image} - {' '.join([self.duration] + self.others)}"

    def replaced_image(self, images_mapping: Dict[str, str]) -> Effect:
        return replace(self, image=images_mapping[self.image])

    @staticmethod
    def parse(line: str) -> Effect:
        key, value = parse_key_value(line)
        duration, *others = value.split(" ")
        return Effect(image=key, duration=duration, others=others)


def to_yes_no(b: bool) -> str:
    return "yes" if b else "no"


def yes_no_to_bool(yes_no: str) -> bool:
    assert yes_no in {"yes", "no"}
    return yes_no == "yes"


@dataclass
class Program:
    effects: List[Effect]
    finish_time: str
    repeat_after_finish: bool = False
    lock_buttons: bool = True

    @property
    def images(self) -> List[str]:
        return [e.image for e in self.effects]

    def replaced_images(self, images_mapping: Dict[str, str]) -> Program:
        return replace(self, effects=[e.replaced_image(images_mapping) for e in self.effects])

    def __str__(self) -> str:
        eff = '\n'.join(f"{e}" for e in self.effects)
        kvs = {
            "Finish": self.finish_time,
            "Repeat after finish": to_yes_no(self.repeat_after_finish),
            "Lock buttons": to_yes_no(self.lock_buttons),
        }
        kvs_str = '\n'.join(f"{k} - {v}" for k, v in kvs.items())
        return f"{eff}\n{kvs_str}"

    @staticmethod
    def parse_file(filename: str) -> Program:
        with open(filename, 'r') as f:
            return Program.parse_lines([line for line in f])

    @staticmethod
    def parse_lines(lines: List[str]) -> Program:
        assert len(lines) > 3

        effects = []
        for line in lines[:-3]:
            try:
                effects.append(Effect.parse(line))
            except Exception as ex:
                raise RuntimeError(f"can't parse effect in line '{line}'") from ex

        def get_value(line: str, expected_key: str) -> str:
            k, v = parse_key_value(line)
            assert k == expected_key, f"can't parse line '{line}', expected key '{expected_key}'"
            return v

        return Program(
            effects=effects,
            finish_time=get_value(lines[-3], "Finish"),
            repeat_after_finish=yes_no_to_bool(get_value(lines[-2], "Repeat after finish")),
            lock_buttons=yes_no_to_bool(get_value(lines[-1], "Lock buttons"))
        )




valid_name_chars: List[str] = list("qwertyuiopasdfghjklzxcvbnm1234567890_")


def filter_valid_chars(name: str) -> str:
    return "".join(c for c in name if c in valid_name_chars)


def is_already_numbered(name: str) -> bool:
    if len(name) < 3: return False
    return name[0].isdigit() and name[1].isdigit() and name[2] == "_" and filter_valid_chars(name) == name


def convert_names(images: List[str]) -> Dict[str, str]:
    used_numbers: Set[int] = set()
    result: Dict[str, str] = {}

    def find_free_number(used: Set[int]):
        for i in range(100):
            if i not in used:
                return i
        return 100

    for image in images:
        if is_already_numbered(image):
            result[image] = image
            number = int(image[:2])
            used_numbers.add(number)

    for image in images:
        if image not in result:
            free_number = find_free_number(used_numbers)
            assert free_number <= 99, "images count > 99"
            result[image] = f"{free_number:02}_{filter_valid_chars(image)[:13]}"
            used_numbers.add(free_number)

    return result


def copy_images(images: Dict[str, str], from_dir: str, to_dir: str):
    for old_name, new_name in images.items():
        from_path = os.path.join(from_dir, f"{old_name}.bmp")
        to_path = os.path.join(to_dir, f"{new_name}.bmp")
        assert os.path.exists(from_path), f"image {from_path} doesn't exist"
        shutil.copy(from_path, to_path)


if __name__ == "__main__":
    args = sys.argv
    if len(args) == 3:
        input_dir = args[1]
        output_dir = args[2]

        prog = Program.parse_file(os.path.join(input_dir, "program.txt"))
        images = convert_names(prog.images)
        new_prog = prog.replaced_images(images)

        os.makedirs(output_dir, exist_ok=True)
        copy_images(images, input_dir, output_dir)
        with open(os.path.join(output_dir, "program.txt"), "w") as f:
            print(f"{new_prog}", file=f)
        print("finished: ok!")
    else:
        print(f"wrong arguments count, example of usage: 'python3 convert.py example/source example/converted'")
