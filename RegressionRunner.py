#!/usr/bin/python

import argparse
import os
import pathlib
import time
import re
from random import randint
from multiprocessing import Process, Queue

import TestRunner as TestRunner


class RegressionRunnerArguments:
    regression_name: str
    regressions_dir: str
    run_dir: str

parser = argparse.ArgumentParser(description="Spawn a batch of tests using a text-based regression list")

parser.add_argument("regression_name", type=str,
                    help="Specify the regression list to run")

parser.add_argument("regressions_dir", type=str, nargs="?",
                    default=os.environ["DV_REGRESSION_LISTS_DIR"],
                    help="Optionally specify where regression the lists are found (default to $DV_REGRESSION_LISTS_DIR) ")

parser.add_argument("--run_dir", type=str,
                    default=os.environ["WORKDIR"] + "/regressions",
                    help="Optionally specify the base run directory (defaults to $WORKDIR/regressions)")



def create_regression_path(run_dir: str, regression_name: str) -> pathlib.Path:
    now: float = time.time()
    formatted_time_str = time.strftime("%Y-%m-%d--%H-%M-%S", time.localtime(now))

    regression_run_path = pathlib.Path(f"{run_dir}/{regression_name}--{formatted_time_str}")

    if regression_run_path.exists(): return regression_run_path

    regression_run_path.mkdir(parents=True)

    return regression_run_path



def parse_regression_file(regressions_dir: str, regression_name: str, regression_run_path: pathlib.Path) -> list[TestRunner.TestRunnerArguments]:
    regression_file_path = pathlib.Path(f"{regressions_dir}/{regression_name}")
    test_runner_parser = argparse.ArgumentParser()
    TestRunner.add_arguments_to_argument_parser(test_runner_parser)
    command_args: list[str]
    test_args: list[TestRunner.TestRunnerArguments] = []


    with regression_file_path.open("r", encoding="utf-8") as r:
        for line in r:
            line = re.sub(r"#.*$", r"", line)
            line = line.strip().lower()
            if line.isspace() or line == "":
                continue # Skip empty lines or lines that were only comments

            command_args = line.split()

            test_args.append(
                test_runner_parser.parse_args(
                    command_args,
                    namespace=TestRunner.TestRunnerArguments()
                )
            )

            test_args[-1].run_dir = str(regression_run_path)
            if test_args[-1].seed == None:
                test_args[-1].seed = randint(0, 4294967295)

    return test_args


def run_test_wrapper(q: Queue, args: TestRunner.TestRunnerArguments) -> None:
    result = TestRunner.run_test(args)
    q.put((args.test_name, args.seed, result))
    print(f"{args.test_name} finished with {result} code")




def run_regression(args: RegressionRunnerArguments) -> None:
    regression_run_path: pathlib.Path
    tests_and_arguments_to_run: list[TestRunner.TestRunnerArguments]

    regression_run_path = create_regression_path(args.run_dir, args.regression_name)
    tests_and_arguments_to_run = parse_regression_file(args.regressions_dir, args.regression_name, regression_run_path)
    test_results: list[TestRunner.TestResult] = []

    summary_file_path: pathlib.Path = regression_run_path / "results.txt"

    jobs: list[Process] = []
    queue: Queue = Queue()

    print("----------------------------")
    print(f"{args.regression_name} regression tests")
    print("----------------------------")

    test_list: list[tuple[str, int]] = [(c.test_name, c.seed) for c in tests_and_arguments_to_run]
    for test_name, seed in test_list:
        print(f"{test_name}({seed})")
    print("")

    for cmd in tests_and_arguments_to_run:
        p = Process(target=run_test_wrapper, args=(queue, cmd))
        jobs.append(p)
        p.start()

    for j in jobs:
        j.join()

    print("")

    print("----------------------------")
    print("     ALL JOBS FINISHED      ")
    print("----------------------------")

    with summary_file_path.open("w", encoding="utf-8") as s:
        while not queue.empty():
            test_name, seed, result = queue.get()
            result_str = f"{test_name:<20}({seed:>10d}) : {result.name}"
            print(result_str)
            s.write(result_str)

    if all(r == TestRunner.TestResult.PASS for r in test_results):
        print("PASS")
    else:
        print("FAIL")


    return


def main() -> None:
    args: RegressionRunnerArguments
    args = parser.parse_args(namespace=RegressionRunnerArguments())
    run_regression(args)



if __name__ == "__main__":
    main()
