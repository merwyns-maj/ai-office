---
name: designer-playbook
description: How Dinda designs UI, motion and the 3D office: glanceable status, purposeful motion, light three.js scenes, reduced motion. Use whenever a task has a UX design section.
---
# Designer playbook

Every rule line ends with a source URL or the words "office rule". A rule with neither is a bug: fix or delete it. Findings below come from the sources named; see Sources for how each was read.

## 1. Who and what it is for
- Design for one audience; a dashboard that tries to serve several serves none. https://doc.arcgis.com/en/dashboards/reference/author-effective-dashboards.htm
- Know where it is viewed: a dim room points to a dark theme. https://doc.arcgis.com/en/dashboards/reference/author-effective-dashboards.htm
- Non-essential elements distract; leave them out. https://doc.arcgis.com/en/dashboards/reference/author-effective-dashboards.htm
- One screen answers one question; write the question at the top of the UX design. office rule

## 2. Ambient status displays
- Map the plan into Done / Running Now / Next so a glance shows where the work is. https://arxiv.org/pdf/2609.33113
- An active item shows a "running" state, the files it touches and a one-line activity summary. https://arxiv.org/pdf/2609.33113
- Keep "running" and "needs attention" visibly different: an item that is asking the human switches to a yellow blinking needs_attention state. https://arxiv.org/pdf/2609.33113
- A top strip with one segment per agent, coloured by lifecycle state, plus counts. https://arxiv.org/pdf/2610.21538
- List agents sorted by how much attention they need, with a live event stream beside the list. https://arxiv.org/pdf/2610.21538
- "Waiting for Merwyn" is the most visible state on any screen; design it first. office rule

## 3. Motion
- Disney's 12 principles combine physics with cognitive psychology to produce emotion, and apply to UI. https://ixdf.org/literature/article/ui-animation-how-to-apply-disney-s-12-principles-of-animation-to-ui-design
- The 12 principles solved realistic motion; UI is a different medium and needs its own principles,. https://medium.com/ux-in-motion/ui-animation-principles-disney-is-dead-8bf6c66207f9
- Use easing: it reinforces "rightness" and UI without easing feels clunky. https://medium.com/ux-in-motion/ui-animation-principles-disney-is-dead-8bf6c66207f9
- Each motion names its purpose (continuity, relationship, attention). A motion with no purpose is removed. office rule
- Any duration or easing figure is a starting value to be judged on screen, not a sourced number. office rule

## 4. Low-poly three.js scenes
- Keep the scene lightweight and minimise polygons on screen; low-poly models cut triangles and CPU/GPU load. https://tympanus.net/codrops/2025/02/11/building-efficient-three-js-scenes-optimize-performance-while-maintaining-quality/
- Compress assets (Draco, pruning, resizing): the article reports about 90% smaller files. https://tympanus.net/codrops/2025/02/11/building-efficient-three-js-scenes-optimize-performance-while-maintaining-quality/
- `antialias: false` can help performance at a quality cost; decide per scene. https://tympanus.net/codrops/2025/02/11/building-efficient-three-js-scenes-optimize-performance-while-maintaining-quality/
- Cut draw calls by joining geometry and re-UVing to one shared texture. https://discourse.threejs.org/t/how-do-i-handle-lag-in-my-scene/7883
- Update far characters less often and keep close ones smooth. https://discourse.threejs.org/t/one-draw-call-massive-crowd-performance-engineering-in-three-js/89928
- Load lighting baked into textures; baked shadows avoid a dynamic shadow map. https://tympanus.net/codrops/2022/04/25/case-study-windland-an-immersive-three-js-experience/
- Target for the 3D office: 8 agents at a smooth frame rate on a laptop. office rule

## 5. Accessibility, including reduced motion
- Let users turn off motion triggered by their own interaction; WCAG 2.3.3 (Animation from Interactions) allows essential animation. https://www.w3.org/WAI/WCAG21/Understanding/animation-from-interactions
- In CSS, detect `prefers-reduced-motion` and disable or replace the motion (technique C39). https://www.w3.org/WAI/WCAG22/Techniques/css/C39
- In script, including three.js render loops, read `window.matchMedia('(prefers-reduced-motion: reduce)')` and stop or simplify the motion (technique SCR40). https://www.w3.org/WAI/WCAG22/Techniques/client-side-script/SCR40
- Every animation has a still or reduced version, written next to it in the UX design. office rule
- No state is shown by colour or motion alone; add a shape, label or position. office rule

## 6. Writing the UX design section
- Order: layout and hierarchy; states; motion per event with its reduced-motion version; visual spec from theme.yaml; accessibility check; open questions with who can answer. office rule
- Hand the result to the builder with design:design-handoff. office rule
- Sign "— Dinda (designer)", leave status and owner alone, and let Fang accept it into Design. office rule

## Sources
Read directly by the Engineer: none. The build sandbox blocked all twelve hosts (proxy 403 on 25 Nov 2026), so every rule above is written from search findings recorded in T-047 Build notes, not from the full pages. Re-check against the page when a rule matters. The three.js forum report on about 25 skinned low-poly characters at 120 fps (a different thread, URL not given) is left out because it has no URL in the source set.
- https://tympanus.net/codrops/2025/02/11/building-efficient-three-js-scenes-optimize-performance-while-maintaining-quality/
- https://discourse.threejs.org/t/one-draw-call-massive-crowd-performance-engineering-in-three-js/89928
- https://discourse.threejs.org/t/how-do-i-handle-lag-in-my-scene/7883
- https://tympanus.net/codrops/2022/04/25/case-study-windland-an-immersive-three-js-experience/
- https://ixdf.org/literature/article/ui-animation-how-to-apply-disney-s-12-principles-of-animation-to-ui-design
- https://medium.com/ux-in-motion/ui-animation-principles-disney-is-dead-8bf6c66207f9
- https://arxiv.org/pdf/2609.33113
- https://arxiv.org/pdf/2610.21538
- https://doc.arcgis.com/en/dashboards/reference/author-effective-dashboards.htm
- https://www.w3.org/WAI/WCAG21/Understanding/animation-from-interactions
- https://www.w3.org/WAI/WCAG22/Techniques/css/C39
- https://www.w3.org/WAI/WCAG22/Techniques/client-side-script/SCR40
