# Transformer Block From Scratch

> One block is the unit of every modern decoder LLM. Layer norm, multi head attention, residual, MLP, residual. The pre-LN variant trains stably without warmup. The post-LN variant is what the original paper shipped. This lesson builds both, side by side, and shows which one survives a 12 layer stack at common learning rates.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 19 lessons 30 to 33 (tokenizer, embeddings, attention math, batched data loader)
**Time:** ~90 minutes

## Learning Objectives

- Build a transformer block in PyTorch from the four moving pieces: LayerNorm, multi head causal attention, residual connections, position wise MLP.
- Place the LayerNorms in two configurations (pre-LN and post-LN) and explain why one trains stably without warmup.
- Implement causal masking inside the multi head attention so token i cannot see tokens j > i.
- Track gradient flow through both variants on a 12 layer stack and read the result without hand waving.
- Reuse the block as a drop-in unit when the next lesson assembles a 124 million parameter GPT.

## The Problem

A transformer is one block repeated. Get the block wrong once, repeat it twelve times, and you ship a model that diverges in the first epoch or that needs warmup hacks the rest of the way. The two failure modes you will see in this lesson are not exotic. They show up the first time a learner stacks blocks naively. One is the attention layer attending to the future. The other is the LayerNorm placed where it cannot tame the residual signal at depth.

The fix is mechanical once you see it. The block has exactly two residual paths and exactly two normalization positions. Choose the positions correctly and the rest of the stack is just bookkeeping.
