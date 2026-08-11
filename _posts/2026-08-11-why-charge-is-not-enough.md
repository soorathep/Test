---
title: "Why Charge Is Not Enough"
date: 2026-08-11 09:00:00 +0700
description: "Mg²⁺ and Zn²⁺ carry the same formal charge, yet behave very differently. Coordination chemistry gives an ion its electrochemical identity."
tag: Research Note
kind: essay
series: "Research Notes"
permalink: /research/why-charge-is-not-enough/
---

### Coordination chemistry gives an ion its electrochemical identity

A lithium ion carries a charge of +1. A sodium ion does too. Magnesium and zinc both carry +2. It is tempting to think that ionic charge and size should tell us how these ions behave in an electrolyte.

They do not.

Consider Mg²⁺ and Zn²⁺. Both are divalent, and their ionic sizes are comparable. Yet their electrochemical behavior can be remarkably different. Mg²⁺ strongly binds its surrounding ligands and often pays a substantial energetic and kinetic penalty when its coordination shell must reorganize near an electrode. Zn²⁺, in contrast, can access a wider range of coordination environments, with water, anions, and additives competing to define the species that actually reaches the interface.

The difference is not simply charge. It is coordination chemistry.

## An ion rarely travels alone

When we write an electrochemical reaction as

<div class="equation" role="img" aria-label="M z plus plus z electrons yields M">
M<sup>z+</sup> + ze<sup>−</sup> → M
</div>

the notation hides much of the chemistry.

In an electrolyte, the reacting species is rarely a bare M<sup>z+</sup>. It exists within a local coordination environment containing solvent molecules, anions, and sometimes specifically designed ligands or additives.

A more realistic starting point is therefore something like

<div class="equation" role="img" aria-label="A metal ion coordinated by x solvent molecules and y anions">
M<sup>z+</sup>(solvent)<sub>x</sub>(anion)<sub>y</sub>
</div>

and *x* and *y* are not merely structural details. They influence how the ion moves, how easily its coordination shell can reorganize, what reaches the electrode surface, and what ultimately reacts there.

## The periodic table does not tell the whole story

Across common battery charge carriers, coordination behavior changes substantially.

Li⁺ is small and forms a compact solvation environment, commonly dominated by oxygen donors. Na⁺ is larger and generally supports a more flexible coordination shell with higher coordination numbers.

Moving to divalent ions changes the problem. Mg²⁺ combines small size with +2 charge, producing strong interactions with surrounding ligands and a relatively persistent first coordination shell. This can make coordination-shell reorganization and desolvation major kinetic barriers.

Zn²⁺ provides an instructive counterexample. It has the same formal charge as Mg²⁺, but its coordination landscape is considerably more diverse. Coordination numbers and geometries can change with solvent, anion, concentration, and additives. For Zn electrochemistry, controlling *which species exists* can therefore be as important as controlling how fast that species moves.

Al³⁺ takes the trend further. Its high charge density strongly polarizes coordinated molecules. In water, coordination is no longer merely a question of solvation: it can drive hydrolysis and change the chemical identity of the species itself.

These comparisons suggest that ionic charge and radius are useful starting descriptors, but not sufficient ones.

## Structure is only the beginning

Even coordination number does not tell the complete story.

Two ions may both have six coordinating oxygen atoms and still behave very differently. We also need to ask:

- How strongly are the ligands bound?
- How rapidly do they exchange?
- How easily can the coordination geometry reorganize?
- How much does anion participation change with concentration?
- What happens to the coordination shell in an interfacial electric field?

This distinction is important because

<div class="equation">
coordination number ≠ coordination strength ≠ coordination dynamics
</div>

The relevant quantity is therefore not a single coordination structure, but a **coordination landscape**: the accessible structures, their relative free energies, and the pathways connecting them.

## From coordination to electrochemistry

This leads to a causal sequence:

<div class="causal-sequence" aria-label="Ion identity leads to coordination landscape, transport, interfacial reorganization, and electrochemical reaction">
  <span class="step">Ion identity</span><span class="arrow">→</span>
  <span class="step">Coordination landscape</span><span class="arrow">→</span>
  <span class="step">Transport</span><span class="arrow">→</span>
  <span class="step">Interfacial reorganization</span><span class="arrow">→</span>
  <span class="step">Electrochemical reaction</span>
</div>

The first coordination shell determines what the ion carries with it through the electrolyte. Transport determines how that coordinated species reaches the interface. Near the electrode, the coordination environment must reorganize again before electron transfer, insertion, or metal deposition can occur.

The species observed in the bulk electrolyte is therefore not necessarily the species that reacts at the electrode.

That distinction matters.

An electrolyte can have high ionic conductivity while presenting an unfavorable coordination environment for interfacial charge transfer. Conversely, modifying an anion or adding a ligand may improve electrochemical reversibility even when bulk conductivity decreases.

The fastest electrolyte is not necessarily the best electrolyte.

## Coordination–Transport–Interface

This is why we place **Coordination** at the beginning of our Coordination–Transport–Interface (CTI) framework.

<div class="causal-sequence" aria-label="Coordination leads to transport and then interface">
  <span class="step">Coordination</span><span class="arrow">→</span>
  <span class="step">Transport</span><span class="arrow">→</span>
  <span class="step">Interface</span>
</div>

Coordination asks what chemical state the charge carrier actually occupies.

Transport asks how that state moves and evolves through the electrolyte.

Interface asks what remains of that coordination environment when the ion encounters an electrode and undergoes electrochemical transformation.

Li⁺, Na⁺, Mg²⁺, Zn²⁺, and Al³⁺ provide different answers to these questions. Comparing them may reveal something more general than the behavior of any individual battery chemistry.

It may reveal why an ion's electrochemical identity is determined not only by what it **is**, but also by what it is **coordinated to**.
