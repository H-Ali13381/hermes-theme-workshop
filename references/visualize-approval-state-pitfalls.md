# Step 2.5 visualize approval/state pitfalls

Session example: `rice-20260503-0538-02e8ee` while iterating a KDE Bonfire Hollow / Dark Souls style rice.

## What happened

The user approved a generated Step 2.5 concept after several regenerate/free-form feedback loops. The bridge call sent the exact answer `approve`, but stdout showed the visualize node first generated a fresh FAL image and multimodal analysis, then logged approval:

```text
02:24:42 [INFO] ricer.visualize: visualize invocation #6
02:24:42 [INFO] ricer.visualize: generating FAL nano-banana image — prompt: Full Linux desktop theme concept preview for bonfire-hollow...
02:24:50 [INFO] ricer.visualize: FAL image generated: https://v3b.fal.media/files/b/0a98b104/agkri1DevstXj6OvhUgq1_Du3z6GbX.png
02:25:03 [INFO] ricer.visualize: multimodal analysis successful
02:25:03 [INFO] ricer.visualize: AI desktop preview approved
```

The previously surfaced image was different. So the approved image was the last URL generated during the approval call, not necessarily the preview the user had just inspected.

## Why it matters

For visual design, the concept image is the creative source of truth. Accidentally claiming the old image is approved can mislead the user and anchor the design to the wrong reference.

## How to handle

1. At every Step 2.5 approval response, read stdout for `FAL image generated:` immediately before `AI desktop preview approved`.
2. If a fresh image appears during the approval call, state that exact URL as the approved image and reopen the resulting preview if appropriate.
3. If the user wanted the previous image specifically, do not pretend it is locked; ask whether to regenerate/backtrack or proceed with the newly approved image.
4. For implementation caveats such as "keep wallpaper manual/user-swappable", do not pass a caveated approval to Step 2.5. The node treats non-exact approval as feedback and regenerates. Send exact `approve`, then carry the caveat into Step 4 plan feedback.

## Related Step 2.5 control strings

Exact approvals: `approve`, `yes`, `ok`, `looks good`, `good`.

Direction revision: `back`, `revise`, `direction`, `explore`.

Everything else is interpreted as feedback and routes to regeneration.
