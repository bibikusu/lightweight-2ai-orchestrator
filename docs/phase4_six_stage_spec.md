# Phase4 Six Stage Specification

## Purpose
Phase4 introduces cross-validation between six fixed stages so that AI outputs are verified by other stages before human final approval.

## Six Stages
- B1 Input Gate
- B2 Spec Layer
- B3 Implementation Layer
- B4 Patch Layer
- B5 Validation Layer
- B6 Report Layer

## Vertical Flow
B1 -> B2 -> B3 -> B4 -> B5 -> B6

## Cross Validation Model
- validator = plaintiff
- target = defendant
- decision logic = judge

## Core 12 Cells
- B2->B3
- B3->B2
- B3->B4
- B4->B3
- B4->B5
- B5->B4
- B5->B2
- B2->B5
- B5->B6
- B6->B5
- B1->B2
- B1->B6

## Completion Rule
Pass only if:
- core 12 cells are represented
- cross validation is machine-readable
- existing 4-command gate passes
- no regression

## Expansion Policy
Phase4-1 = 12 cells
Phase4-2 = selective expansion
Phase4-3 = 36 cells
