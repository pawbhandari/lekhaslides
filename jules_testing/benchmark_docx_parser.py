import timeit
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.docx_parser import clean_markdown_artifacts, parse_lines

def benchmark_clean_markdown_artifacts():
    test_str = "**bold text** and __more bold__ and *italic* and _underscore_"
    # Run a simple benchmark
    n_iterations = 100000
    timer = timeit.Timer(lambda: clean_markdown_artifacts(test_str))
    execution_time = timer.timeit(number=n_iterations)
    print(f"clean_markdown_artifacts: {n_iterations} iterations took {execution_time:.4f} seconds")

def benchmark_parse_lines():
    lines = [
        "1. **Question** one with __bold__ and *italic*",
        "A) **Option** A",
        "B) Option B",
        "2. Question two",
        "A. Option A",
        "B. Option B",
    ] * 1000 # 6000 lines

    timer = timeit.Timer(lambda: parse_lines(iter(lines)))
    execution_time = timer.timeit(number=10)
    print(f"parse_lines: 10 iterations of 6000 lines took {execution_time:.4f} seconds")

if __name__ == "__main__":
    print("Baseline Benchmarks:")
    benchmark_clean_markdown_artifacts()
    benchmark_parse_lines()
