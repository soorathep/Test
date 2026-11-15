# 2105315 Data Analytics labs

Interactive labs for 2105315 Data Analytics in Chemical Engineering (weeks 1 to 7, before the midterm).
Source here; `build.py` publishes to `teaching/2105315/labs/` (and refreshes the shared kit first).

From 2026/2 students do not write code from scratch. They learn the principle in the lab, let an AI
assistant write notebook code, and check that code. Each lab therefore has:

- a short incident and one question;
- a prediction before the reveal (Lab 01: eight statements about the file);
- "Check the AI's code": plausible code with one realistic error, answered in writing before the explanation opens;
- notebook numbers: the student runs AI-written code on their own data file and enters the results; the lab,
  which computes the same quantities independently in JavaScript, is the reference;
- a data set chosen from the student ID, so numbers differ between students;
- one JSON study file for submission on myCourseVille (questions, answers, choices, results).

## Lab 01 · Is this file ready for the morning report?

Data: UCI Air Quality (De Vito, doi:10.24432/C59K5F, CC BY 4.0), hourly, March 2004 to April 2005.
`tools/make_airquality.py` builds `assets/data/airquality.json` from the UCI file and checks its sha256.
Each student gets a 14-day window starting at any hour (about 9,000 choices) with three repeated rows
inserted. The repeats are the only change to the data; the page says so.

Checks before each push:

    python3 _teaching-src/2105315/labs/build.py
    python3 _teaching-src/2105315/labs/tests/smoke_test.py         # Playwright, desktop and 375 px
    python3 _teaching-src/2105315/labs/tests/engine_vs_pandas.py   # needs Node.js; engine = pandas

## Grading

The study file carries the question text with each answer, so it can be read by a person or by an AI
grader. `audit` and `notebook.reference` are computed by the page; the file can be edited by a student, so
recompute from `dataset.startIndex` and `dataset.repeatedBlockAt` when a number matters. A `dataset.seedId`
that differs from `student.studentId` means the work was done on someone else's data set. Keep rubrics and
answer keys outside this public repository.
