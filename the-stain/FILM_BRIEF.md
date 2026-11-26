# THE STAIN (รอยเปื้อน) — 3D Animated Short Film: Production Brief for Claude Code

This file has three parts:

- **Part A: phone setup.** Do this once, on your phone.
- **Part B: the prompts.** Copy and paste these into Claude Code.
- **Part C: the production brief** (sections 1–12). Claude Code reads this and follows it.

---

# PART A — Setup on your phone (one time, about 20 minutes)

Claude Code started from the Claude phone app runs in a **cloud session** on Anthropic's computers, not on your phone. It works with a GitHub repository, so everything is saved there, and you watch the results on GitHub.

1. **Make a GitHub account and a repository.** In your phone's browser, go to github.com, sign up, and create a new **private** repository called `the-stain`. Tick "Add a README file."
2. **Upload this file and your song.** In the repository, tap **Add file → Upload files**:
   - this file, renamed to **`FILM_BRIEF.md`**
   - your ending song, renamed to **`song.mp3`** (or `song.wav`)

   Then tap **Commit changes**. (Claude Code will move the song into `assets/`.)
3. **Connect GitHub to Claude Code.** In the Claude app, open **Code**, sign in with GitHub when asked, and allow access to the `the-stain` repository.
4. **Create a cloud environment** (from the environment selector when you start a new Code session: **Add cloud environment**):
   - **Name:** `film`
   - **Network access:** **Custom**. Tick **"Also include default list of common package managers"**, and add these domains, one per line:
     ```
     download.blender.org
     speech.platform.bing.com
     api.elevenlabs.io
     ```
     The first is for Blender, the second for the free Thai voices, and the third only matters if you use ElevenLabs.
   - **Environment variables** (only if you have an ElevenLabs key; otherwise leave this empty):
     ```
     ELEVENLABS_API_KEY=your_key_here
     ```
   - **Setup script:** paste this whole block.
     ```bash
     #!/bin/bash
     # Installs Blender (headless), ffmpeg and the Thai voice tool. Safe to re-run.
     apt-get update -qq || true
     apt-get install -y -qq ffmpeg libxi6 libxkbcommon0 libsm6 libxrender1 libxxf86vm1 libxfixes3 libgl1 libegl1 fonts-noto-core || true
     if [ ! -x /opt/blender/blender ]; then
       cd /opt && curl -fsSL -o blender.tar.xz https://download.blender.org/release/Blender4.2/blender-4.2.3-linux-x64.tar.xz \
         && tar -xf blender.tar.xz && mv blender-4.2.3-linux-x64 /opt/blender && rm -f blender.tar.xz || true
     fi
     ln -sf /opt/blender/blender /usr/local/bin/blender || true
     pip install -q --break-system-packages edge-tts pydub imageio-ffmpeg || true
     exit 0
     ```
5. **Start a session** in the `film` environment on the `the-stain` repository, and paste **Prompt 1** from Part B.

**Good to know**

- **There's no graphics card in the cloud.** Rendering is slow, so the brief is tuned for it: 1280×720, animated "on twos" like stop-motion, and long renders split into small chunks. The final render can still take a day or more of session time. Prompt 3 lets Claude keep rendering on a schedule without you.
- **Everything is saved to GitHub** on a branch called `film`. To watch progress, open the GitHub app or website, switch to the `film` branch, and tap any image, MP3 or MP4 under `checkpoints/`.
- **If a session stops or you close the app,** start a new session and paste **Prompt 2**. Claude picks up from `PROGRESS.md`.

---

# PART B — The prompts

## Prompt 1: start the film (paste into the first session)

```
You are the director, 3D artist, animator, sound designer and editor of a short animated film called THE STAIN (รอยเปื้อน). The complete spec is FILM_BRIEF.md in this repository. Read all of it before you do anything else, especially Part C, sections 1–12.

How we work together:

1. I only have my phone. I can't run commands, open Blender or look at files on a computer. Show me everything as files committed to this repo that I can open in the GitHub app: images (PNG/JPG), audio (MP3) and video (MP4 under 25 MB) in checkpoints/. Give me a direct GitHub link to each file, on the `film` branch.

2. This is a cloud session. There's no GPU, about 4 CPUs, 16 GB RAM and 30 GB of disk. A command can run about 10 minutes in the foreground and about 30 more minutes in the background. The VM pauses when idle, and a new session starts from a fresh clone. So:
   - Split every long job (renders, batch voice generation) into resumable chunks that each finish in under about 20 minutes.
   - After every chunk, commit and push. Nothing finished may live only on the VM.
   - Raw PNG frames stay out of git (.gitignore). Commit encoded clips instead, as described in section 11.

3. Use one branch, `film`, for the whole project. At the start of every session: git fetch, check out `film` (create it from the default branch if it doesn't exist), and read PROGRESS.md. After every step, update PROGRESS.md with what's done, what's next, every decision I've made and every approved checkpoint, then push.

4. Follow the phases in section 11 in order. Stop at every CHECKPOINT, show me the results with links, and wait for my approval. Never start the next phase without it.

5. Keep my creative decisions: the story, the Thai dialogue, the shots, the lighting plan, the hum made from my song. If something in the brief can't work in this environment, tell me plainly and propose the closest option. Never simplify it silently.

6. Before you show me any render, open and look at it yourself. Check it against the brief (framing, lighting state, continuity table, character colors), and fix problems first.

7. The Thai dialogue is in section 10. Don't rewrite it unless I ask. If the voice engine mispronounces something, tell me and suggest a respelling for that line only.

8. Keep your messages to me short and phone-friendly: what you did, the links, and what you need from me.

Start with Phase 0 now. Send me all the Phase 0 questions in one message.
```

## Prompt 2: continue in a new session

```
Continue THE STAIN. Check out the `film` branch, read FILM_BRIEF.md and PROGRESS.md, then tell me in three lines where we are and what you'll do next. Keep following all the rules from Prompt 1, which are in Part B of FILM_BRIEF.md. Then carry on.
```

## Prompt 3: automatic rendering on a schedule (optional, only after you approve Checkpoint 5)

Ask Claude Code to "create a scheduled task that runs every hour" with this prompt, or set up a routine in Claude Code:

```
Render the next part of THE STAIN. Check out the `film` branch and read FILM_BRIEF.md (section 11, Phase 5) and PROGRESS.md. Render the next unrendered chunks for at most 40 minutes in total, each chunk under 20 minutes. After each chunk: look at a sample frame and check it against the brief, encode the chunk, commit, push, and update PROGRESS.md. If something looks wrong or fails twice, stop rendering, write the problem at the top of PROGRESS.md, and don't render anything else. When every shot is rendered, write "ALL SHOTS RENDERED" at the top of PROGRESS.md and stop.
```

---

# PART C — Production brief

> **To Claude Code:** Part C is the complete spec for a 3D animated short film, made in code with Blender's Python API, in a cloud session without a GPU.
> Work through the **Phases** in section 11 in order. **Stop at every CHECKPOINT** to show the user stills, audio or video (as committed files with GitHub links), and wait for approval before you continue.
> Treat `shots.json` (which you will generate from section 10) as the single source of truth for timing, cameras and dialogue.
> If something in this brief can't be done in this environment, say so plainly and propose the closest alternative. Never skip it silently.

---

## 1. The film in one paragraph

Four friends, MARTIN, DAO, ANDY and DO, meet at Martin's house for Do's birthday dinner. Strange marks start appearing *before* the events that cause them: a wine stain before the spill, a nosebleed before the punch, a bullet hole before anyone has fired a gun. Out of fear they lock the door and close the curtains, and they trap themselves. A search for the gun exposes everyone's secrets. They fire the gun to "close the loop," but then they find Do's dead body in the hallway, even though Do is still alive and standing next to them. One of them will kill him tonight. The door is open, and nobody leaves.

**Theme:** the paradox never forces anyone to do anything. It only shows them the result. The monsters are the people. This is a modern take on Sartre's *Huis Clos* (*No Exit*): one closed room, everyone needs someone else to believe them, and hell is other people.

**Core rule of the film:** *the effect always comes before the cause*, for the audience as well as the characters. The hum we hear all through the film is a fragment of the song that plays in full only over the end credits.

---

## 2. Format

| Setting | Value |
|---|---|
| Tool | Blender 4.2 LTS, installed at `/opt/blender` by the environment setup script, run headless: `blender -b -P script.py`. If it's missing, install it the same way (see Part A, step 4). |
| Render engine | **Test in Phase 0.** There's no GPU, so first try EEVEE headless (it may work through software OpenGL, slowly). If it fails or takes more than about 20 s per frame at 1280×720, use **Cycles on CPU**: 16–32 samples, OpenImageDenoise, max 4 light bounces, simple materials. Animatic passes use Workbench (or Cycles at 4 samples if Workbench won't run headless). |
| Resolution / fps | Final **1280×720** (cloud, no GPU). Animatic at 640×360. The timeline runs at **24 fps**, but characters are **animated on twos** (12 new poses per second, held for 2 frames each), like stop-motion. **Render only the unique frames** and double them with ffmpeg. This halves render time and suits the clay look. Camera moves can stay on twos as well. |
| Target length | About 8–10 minutes plus credits. The shot estimates add up to about 8 minutes, and natural pauses and breathing room will stretch it. Don't pad it. |
| Language | Thai voices. Thai and English subtitles as separate `.srt` files, plus one burned-in Thai version. |
| Visual style | **Stylized, not realistic.** Think stop-motion or clay-figure feel: simple readable faces, soft materials, strong lighting. Realistic humans made in code look uncanny in a bad way, while stylized figures look intentional. |
| Aspect ratio as storytelling | Render at 16:9 and add animated black mattes in the compositor: **Act 1 = 2.39:1** (wide, open) → **Act 2 = 1.85:1** (the mattes slide in as the curtains close in shot 4E) → **Act 4 = 1.33:1** (snaps in on the body reveal, shot 9A). The frame literally closes in on them. |

---

## 3. Characters

Each character has a signature color so the audience can read who's who in wide shots.

| Character | Age / build | Look | Signature color | Personality on screen | Secret |
|---|---|---|---|---|---|
| **MARTIN (มาร์ติน)** | 29, tall, broad | Short neat hair, rolled sleeves, a jacket he never takes off | Navy blue | Charming host, short fuse | He knows about Dao and Do. There's a ring box in his jacket: he planned to propose to Dao at Do's birthday, in front of Do. |
| **DAO (ดาว)** | 28, slim | Shoulder-length hair, simple deep-red dress, a purse always within reach | Deep wine red | The sharp one, first to understand the paradox | She's sleeping with Do. Her purse holds an unregistered gun, bought because Do threatened to tell Martin if she ended it. |
| **ANDY (แอนดี้)** | 30, average, glasses | Neat, olive/grey shirt, wristwatch | Olive grey | "The pragmatic one," calm and controlling, runs the search like a judge | He owes Do 800,000 baht. His phone shows Do's threats and a one-way flight booked for 07:00 tomorrow. |
| **DO (โด้)** | 28, wiry, restless | Messy hair, **white shirt** (the birthday boy, and the shirt is a "stain magnet" that echoes the tablecloth) | White | The joker, everyone's friend, the victim. Likeable at first, ugly in the middle. | He has leverage over everyone and has been using it. |

### Character build options (ask the user in Phase 0)

- **Option A (only if the user can upload files to the repo):** The user downloads 4 rigged characters plus animation clips (idle seated, talking gestures, standing up, lunging, grappling, falling, sitting down, walking) as FBX from **Mixamo** (free with an Adobe account) into `assets/characters/`. You import them, restyle the materials to the signature colors, add a simple jaw/mouth control for lip sync, and blend the clips with the NLA editor.
- **Option B (default for this phone/cloud setup, fully code-generated):** Build stylized figures procedurally: smooth capsule bodies, rounded heads, large simple eyes, hinged mouths, hair as sculpted shapes. Rig them with a Rigify metarig, and keyframe poses procedurally from the action descriptions in the shot list. Stiffer animation, but zero downloads. A mannequin/puppet look suits the "trapped" theme.

**Lip sync:** drive mouth open/close from each Thai voice line's audio amplitude envelope (this works for any language). If Rhubarb Lip Sync is installed, its `--recognizer phonetic` mode can add mouth shapes. **Eyes:** procedural blinks every 2–6 s, plus eye targets that look at whoever is speaking. Looks between characters are half of the acting in this film.

---

## 4. The set: Martin's house (one location)

Build it to real scale (meters). The film needs only the **living/dining room** and the **entrance hallway**, which must be visible from the dining table.

```
            ┌───────────── WINDOW (big, floor-to-ceiling, heavy curtains) ─────────────┐
            │                                                                          │
            │   SOFA        BOOKSHELF                       FLOOR LAMP                 │
            │                                                                          │
            │                ┌──────────── DINING TABLE (2.2 × 1.0 m) ───┐            │
            │      MARTIN ●  │  white tablecloth, candles, cake, wine,   │ ● ANDY     │
            │                │  4 glasses, vase (center-left)            │  (head)    │
            │       DAO   ●  └───────────────────────────────────────────┘ ● DO       │
            │                                                                          │
            │   SIDEBOARD (speaker, Martin's phone)          WALL CLOCK                │
            └──────────────────────┐                          ┌───────────────────────┘
                                   │   ENTRANCE HALLWAY 1.2 m │  ← one dying ceiling bulb
                                   │   (≈5 m long, tiled)     │
                                   │        FRONT DOOR        │
                                   └──────────────────────────┘
```

- Modern Thai city house: warm wood floor, off-white walls, one textured accent wall.
- **No mirrors anywhere** (a Huis Clos rule). The only reflective surfaces are the black window at night and a dark TV screen.
- Bookshelf: one book spine reads *Huis Clos* (an easter egg; visible in one wide shot, never pointed out).
- Window: night city lights outside (an emissive backdrop plane with bokeh).
- The curtains must be able to close, and they need a modelled bullet-hole state.

### Continuity: prop states (check these before every render)

| Prop | Sc 0–1 | Sc 2–3 | Sc 4–6 | Sc 7–8 | Sc 9–10 |
|---|---|---|---|---|---|
| Tablecloth | White → one wine stain appears (1H), spill lands on it (1K) | + Martin's blood drops | + Andy's pen marks (optional) | same | On the table AND (future copy) over the body in the hallway. New dark stain spreads in 10E. |
| Window | Clean. Cork hits a spot center-left (1D). | Clean | Bullet hole with radial cracks at the exact cork spot | Bullet passes through the hole | Hole |
| Curtains | Open | Open | Closed (4E). The fabric has a matching hole from the start of 4E. | Closed | Closed |
| Vase | On table | On table | Found lying on the floor (5A), Dao puts it back | Knocked off in the struggle, lands in the exact 5A position | On floor |
| Gun | Hidden in Dao's purse | Hidden | Hidden | Out: on the table, then skitters to the floor, then fired | On the rug, then in Do's hand |
| Ring box | Martin's inner jacket pocket | same | Found (6C), left on table | Table | Table |
| Candles | Lit, blown out after the wish (1I), re-lit for dinner | Lit | Burning low | One goes out | Out |
| Front door | Unlocked | Unlocked | Locked by Martin (4D), key in his pocket | Locked | Unlocked and opened (10A) |
| Martin's nose | Clean | Blood (2B), blood again (3C) | Dried blood | same | same |
| Andy's palm | Clean | Clean | Cut appears (5B), never explained | same | same |
| Martin's wrist | Clean | Clean | 3 scratches appear (5C), never explained | same | same |

---

## 5. Lighting plan

The lighting tells the story. The room gets colder and harder as trust breaks down.

| | Act 1: The table (Sc 0–3) | Act 2: The room closes (Sc 4–6) | Acts 3–4: The gun / No exit (Sc 7–10) |
|---|---|---|---|
| Key | Warm pendant over the table, 2700 K, large soft area light | Same pendant, smaller and harder | Pendant **only**, as a hard top light. Eyes fall into shadow. |
| Fill | Two table/floor lamps at 2700 K plus candles at 1800 K | The floor lamp is turned off in the panic (4C). Candles burn low. | Almost none. Contrast is around 10:1. |
| Rim / back | Cool city light through the window, 6500 K blue, soft | **Gone** when the curtains close. Replace it with one thin cold beam through the curtain's bullet hole (volumetric shaft). | The pin beam stays. The hallway bulb is a sickly 4000 K and flickers. |
| Atmosphere | Light haze, bloom on candles | Haze up a little | Haze up. The flicker syncs with the hum. |
| Feeling | A golden, safe dinner party | Interrogation | A cell where the lights never go out |

Render settings: whichever engine Phase 0 picks, aim for the same look. In Cycles, use emissive candle flames, a volume box for haze and clamp indirect light to cut noise. In EEVEE, turn on soft shadows, shadow resolution high, bloom (or the compositor Glare node in 4.2+) low, volumetrics in a box around the room, AgX view transform, a slight film grain in the compositor. Animate the pendant's flicker with a noise F-curve modifier keyed to the hum's timing.

---

## 6. Camera language

| | Act 1 | Act 2 | Act 3–4 |
|---|---|---|---|
| Lenses | 24–35 mm, group shots | 50 mm, pairs and singles, over-the-shoulder | 85 mm close-ups, low headroom. Rarely more than two faces share a frame. |
| Movement | Locked off or slow smooth dolly | Handheld begins at the nosebleed (2B): subtle noise on camera rotation | Handheld, closer. A short Dutch tilt only in the struggles. |
| Depth of field | f/4, everyone readable | f/2.8 | f/1.8–2.0, background melts away |
| Rules | Keep the 180° line across the table | **Break the 180° line in the trial (Sc 6)** with a slow 360° orbit around the table. Nobody has a safe side any more. | Faces fill the frame |

**Signature shots (they must match exactly):**

1. **The hallway frame** (0A and 9A): an identical locked-off camera on the empty hallway, later with the body in it. Duplicate the camera object, never re-place it by hand.
2. **The overhead table** (0B and 10E): a straight top-down 24 mm on the tablecloth. It opens on the clean cloth and closes on the new stain.
3. **Floor-level gun** (7C): a 24 mm lens inches above the rug, the gun in the foreground, slow push-in, then tilt up to the curtain hole.
4. **The pin of light** (from 4E on): the thin cold beam through the curtain hole cuts across the room behind the characters.

---

## 7. Sound design and music

- **The song:** the user uploads their ending song to the repo root as `song.mp3` or `song.wav`. In Phase 0, move it to `assets/` and convert a WAV working copy. If it's missing, ask for it. Don't choose or download a song yourself.
- **The hum** is made *from the song*, with ffmpeg/sox. Take one sustained moment of a few seconds and slow it heavily (around 0.25–0.4×, pitched down), add a low-pass filter (~600 Hz) and long reverb, then loop it seamlessly. Make 5 versions, each a bit **longer, clearer and closer to the original** (`hum_1.wav` … `hum_5.wav`). Use them in order at 2A, 4A, 5B, 9A and 10E. By the end, the audience should almost recognize the song.
- Shot 1A: the song starts **clean** from the party speaker for about 3 s, and Do skips it. This is the cause trying to arrive early.
- Credits: the full song, finally.
- Room tone: Act 1 has city noise through the glass, quiet chatter and cutlery. **When the curtains close (4E) the city noise cuts out**, leaving breathing, the clock ticking, the fridge and the hum. Acts 3–4 are near silence, so every sound is loud.
- Sound effects (generate or ask the user for CC0 files): champagne cork pop plus glass crack, glass knocked over, wine splash, nose hit (muted thud, no gore), lock click, curtain rings sliding, vase falling, gunshot (followed by 3 s of high ringing and muffled sound), phone vibrations.
- Mix: dialogue at about −14 LUFS integrated for the final, and the hum sits under the dialogue but is always *felt*.

---

## 8. Voices (Thai)

| Character | Direction | Default engine: `edge-tts` (free) | Better: ElevenLabs (if the user gives an API key) |
|---|---|---|---|
| MARTIN | Warm, gets louder and cracks when angry | `th-TH-NiwatNeural`, pitch −6 Hz, rate −5% | A deep male voice, multilingual model |
| DAO | Low, controlled, precise. A whisper when she understands. | `th-TH-PremwadeeNeural`, rate −5% | A calm female voice |
| ANDY | Flat, reasonable, slow. Scary because he's calm. | `th-TH-NiwatNeural`, pitch −14 Hz, rate −12% | A low, measured male voice |
| DO | Fast, playful, then raw fear | `th-TH-NiwatNeural`, pitch +10 Hz, rate +8% | A light, energetic male voice |

- edge-tts needs `speech.platform.bing.com` in the environment's allowed domains (Part A, step 4). If it's blocked or refused from the cloud, tell the user and offer ElevenLabs (key in `ELEVENLABS_API_KEY`, domain `api.elevenlabs.io`).
- At runtime, check the Thai voices that actually exist (`edge-tts --list-voices | grep th-TH`) and adjust. With only one Thai male voice in edge-tts, the three men must sound clearly different. If pitch and rate offsets aren't enough, tell the user and recommend ElevenLabs.
- Generate **every line as its own file** (`audio/vo/<shot>_<character>_<n>.wav`). Line durations decide shot lengths. Commit the voice files, which are small.
- Pauses matter as much as lines: add the silences written in the script.
- **The Thai dialogue below should be checked by a native speaker (the user) before generating final audio.** Generate a test batch first (CHECKPOINT 1).

---

## 9. Foreshadowing: the effect-before-cause plants

Each one must read clearly on a second viewing, and **no character ever points one out**.

| Plant (early) | Payoff (late) |
|---|---|
| Song fragment as the hum. Do skips the song in 1A. | The full song over the credits |
| Grey "RIP-style" birthday meme: "HBD ตำนาน 🕊️ 1998 – 2026" | His phone lights up with "RIP ตำนาน 😂" comments in 10E, after we've seen his body |
| Champagne cork hits the window (1D) | Bullet hole in the exact same spot (4A) |
| The wish: "ขอให้คืนนี้ไม่มีวันจบ" (I wish tonight never ends) | It doesn't end. They sit back down (10C). |
| Dao's purse drops with a heavy thud (1F) | The gun (7A) |
| Martin keeps touching his jacket pocket (1G, 2D, 4D) | A ring box, not a weapon (6C). The audience assumed the worst too. |
| Do's toast: "ค่าเหล้าแอนดี้เลี้ยง ยังติดกูอยู่" | Andy's debt (6D) |
| Party game: "who has to go?" Everyone points at Do. | Shots 9B–9E: nobody says it, but we remember |
| Empty hallway shot (0A) | The same shot with the body (9A) |
| The white tablecloth: "เดี๋ยวก็เลอะ" | It becomes his shroud |

---

## 10. The script: shot list with dialogue

Format: **Shot ID** · framing/lens/move · action · **dialogue** (Thai, then English) · approximate duration. Turn this into `shots.json`. Final durations come from the generated voice audio plus the written pauses.

### SCENE 0: COLD OPEN (≈0:25)

- **0-0** · Black · The hum (`hum_1.wav`), 5 s. Nothing else.
- **0A** · **Hallway frame** (locked off, 35 mm, eye level, from the living room end) · The empty tiled hallway, front door at the far end. The ceiling bulb flickers once. Hold the shot a beat too long. Off screen: the snap of a tablecloth being shaken out. · ~9 s
  - MARTIN (O.S.): **"ไฟตรงทางเดินกะพริบมาทั้งอาทิตย์แล้ว"** (That hallway light's been flickering all week.)
- **0B** · **Overhead table** (top-down 24 mm) · A white tablecloth floats down and settles. Dao's hands smooth it flat. Pure white fills the frame. · ~8 s
  - DAO: **"ใครเขาปูผ้าขาวกินไวน์แดงกันเนี่ย"** (Who puts out a white cloth with red wine?)
  - ANDY (O.S.): **"เดี๋ยวก็เลอะ"** (It's going to get ruined.)
- **0C** · Title card on black: **THE STAIN / รอยเปื้อน** · 3 s

### ACT 1: THE TABLE (2.39:1)

#### SCENE 1: THE STAIN (≈1:50)

- **1A** · Wide master, 24 mm, slow dolly in from the window side · All four at the table, the city glittering behind the open curtains, candles, warm chaos. The song starts clean from the sideboard speaker. Do reaches over and skips it. Laughter. · ~10 s
  - DO: **"เพลงเศร้าไปป่ะ วันเกิดกูนะเว้ย"** (Bit sad, no? It's my birthday.)
- **1B** · Insert, 50 mm, Dao's phone screen · The meme: a greyscale photo of Do with cartoon angel wings and clouds, the text **"HBD ตำนาน 🕊️"** and **"1998 – 2026"**, styled like a memorial post. · ~4 s
- **1C** · Medium 4-shot, 35 mm · The phone goes around. Everyone howls. Do laughs the hardest. · ~8 s
  - MARTIN: **"ใครโพสต์วะเนี่ย"** (Who posted this?)
  - ANDY: **"ไอ้เต้ยที่ออฟฟิศ"** (Tey from the office.)
  - DO: **"รีโพสต์เลย ตายตาหลับละกู"** (Repost it. Now I can die happy.)
- **1D** · Medium on Do, then insert on the window · Do pops the champagne. The cork shoots past Martin's head and **cracks against the window, center-left**. A tiny scuff. Cheers. · ~7 s
  - DAO: **"กระจกแตกป่ะ"** (Did it crack?)
  - MARTIN: **"ไม่เป็นไร ๆ"** (It's fine, it's fine.)
- **1E** · Do stands for a toast, 35 mm, slightly low angle. Cut to reaction singles. · ~20 s
  - DO: **"ขอบคุณที่มากันนะ... มาร์ติน ขอบใจที่ให้ยืมบ้าน... ดาว... คนที่รู้ใจกูที่สุด"** (Thanks for coming... Martin, thanks for the house... Dao... the one who knows me best.)
  - *(Beat. Close-up on Martin: his jaw tightens for half a second. Close-up on Dao: her eyes drop.)*
  - DO: **"แล้วก็แอนดี้ คืนนี้ค่าเหล้าแอนดี้เลี้ยง ยังติดกูอยู่นี่หว่า"** (And Andy, drinks tonight are on Andy. He still owes me.)
  - ALL: **"ชน!"** (Cheers!) *Close-up on Andy: the only one not laughing.*
- **1F** · Medium on Dao · She hangs her purse on her chair. It slips and hits the floor with a heavy THUD that is much too loud. · ~6 s
  - ANDY: **"ในกระเป๋ามีอะไรวะ อิฐเหรอ"** (What's in there, a brick?)
  - DAO *(laughing it off, putting the purse on her lap)*: **"เรื่องของผู้หญิงน่า"** (Girl stuff.)
- **1G** · Close-up, 85 mm, Martin's hand · He touches his jacket pocket, checking something is still there. · 2 s
- **1H** · Close-up on the tablecloth, then medium on Martin · **A red wine stain is already on the white cloth.** Martin frowns, rubs it, smells his finger. Insert: his glass is empty. Rack focus behind him: Andy is *only now* twisting the corkscrew into the red wine. · ~10 s
  - MARTIN: **"ใครทำไวน์หกเนี่ย"** (Who spilled wine?)
  - ANDY: **"เพิ่งจะเปิดเนี่ย"** (I'm only just opening it.)
  - DO: **"ยังไม่มีใครรินเลยด้วยซ้ำ"** (Nobody's even poured yet.) *They shrug it off.*
- **1I** · The lights go down and the cake comes in. Wide, then a close-up of Do lit by candles · A short "สุขสันต์วันเกิด" (the traditional birthday song, which is public domain), then Do closes his eyes. · ~15 s
  - DO: **"ขอให้คืนนี้... ไม่มีวันจบ"** (I wish tonight... never ends.) *He blows out the candles.*
  - ANDY *(quietly, smiling)*: **"ระวังปากหน่อย"** (Careful what you wish for.)
- **1J** · 4-shot, 35 mm · Dao starts a game. · ~14 s
  - DAO: **"เล่นเกมกัน ถ้าเราติดอยู่ในห้องนี้ แล้วต้องมีคนนึง 'ไป'... จะเลือกใคร นับสาม"** (Game: if we were stuck in this room and one of us had to "go"... who? On three.)
  - ALL: **"หนึ่ง สอง สาม!"** *All three point at Do at once. Huge laugh.*
  - DO *(raising his glass)*: **"ยุติธรรมดี"** (Fair.)
- **1K** · Medium 2-shot of Andy and Do, then a slow-motion insert (48 fps feel) · Do lands a punchline. Andy laughs too hard and knocks his glass over. The wine arcs and lands **exactly on the existing stain**, filling its shape perfectly. A beat, then laughter. · ~10 s
  - MARTIN: **"เดจาวูว่ะ"** (Déjà vu.)
  - DAO *(not laughing, looking at the stain)*: **"บังเอิญน่า"** (Coincidence.)

#### SCENE 2: THE NOSEBLEED (≈0:25)

- **2A** · Wide · `hum_2` rises out of nowhere. The pendant flickers. Everyone goes still. Then it stops. · ~6 s
- **2B** · Close-up on Martin, **handheld begins here** · His head snaps back as if punched. Blood runs from his nose (stylized and dark, not gory). · ~4 s
  - MARTIN: **"โอ๊ย! ใครต่อยกูวะ!"** (Ow! Who hit me?!)
- **2C** · Fast whip pans across the faces · · ~6 s
  - ANDY: **"ไม่มีใครแตะมึงเลย"** (Nobody touched you.)
  - DO: **"นั่งห่างตั้งสองเมตร"** (We're two meters away.)
- **2D** · Medium on Martin pressing a napkin to his nose. Drops of blood hit the tablecloth. Close-up: his hand checks his jacket pocket again. Dao watches Do and Do watches Martin. · ~8 s

#### SCENE 3: THE REALIZATION (≈0:35)

- **3A** · Over-the-shoulder on Do, 50 mm · · ~4 s
  - DO *(smirking)*: **"เล่นใหญ่ไปไหม ดาราเลยนะมึง"** (A bit dramatic, aren't you? A real movie star.)
- **3B** · Close-up on Martin · · ~5 s
  - MARTIN *(low)*: **"มึงรู้ตัวดีว่ามึงทำอะไรไว้"** (You know exactly what you've done.)
  - DAO *(a warning)*: **"มาร์ติน..."**
- **3C** · Medium 2-shot, cut on action · Martin lunges across the corner of the table. Do's elbow flies up in reflex. Cut on impact (show the motion and a sound, no gore). Martin stumbles back, **bleeding from the nose in exactly the same way**. · ~4 s
- **3D** · Wide, static, total silence · Nobody moves for 3 s. · ~3 s
- **3E** · Slow push-in on Dao, 50 mm · · ~14 s
  - DAO *(barely audible)*: **"มันมาก่อน... เลือดมันออกก่อนที่จะโดน"** (It came first... the blood came before the hit.)
  - ANDY: **"พูดอะไรของแก"** (What are you talking about?)
  - DAO: **"รอยไวน์ด้วย มันเปื้อนก่อนที่แก้วจะหก... ผลมันมาก่อนเหตุ"** (The wine too. It stained before the glass fell... the effect comes before the cause.)
- **3F** · Medium on Martin · He grabs his jacket and heads for the hallway. · ~3 s
  - MARTIN: **"กูไม่อยู่แล้ว"** (I'm out.)

### ACT 2: THE ROOM CLOSES (the mattes slide to 1.85:1 during 4E)

#### SCENE 4: THE BULLET HOLE (≈0:55)

- **4A** · Medium on Andy, then a slow push-in on the window, 50 mm · `hum_3` starts. · ~8 s
  - ANDY: **"เดี๋ยว! ...หน้าต่าง"** (Wait! ...The window.)
  - *There's a **bullet hole with radial cracks in the glass, exactly where the cork hit.***
- **4B** · Four quick singles · Reactions. · ~4 s
- **4C** · Medium wide · Do knocks the floor lamp over as he spins round (fill light dies). · ~6 s
  - DO: **"ใครมีปืน"** (Who has a gun?) *Silence.* **"ใครมีปืน!"** (WHO HAS A GUN?!)
  - *Close-up: Dao's hands tighten on the purse in her lap.*
- **4D** · Martin walks to the hallway door, locks it, and pockets the key. Close-up of the key going into the jacket, next to the pocket he keeps touching. · ~6 s
  - MARTIN: **"มีคนอยู่ข้างนอก"** (Someone's outside.)
- **4E** · Medium on Dao at the window · She pulls the heavy curtains shut. The city noise cuts out, and **the mattes slide in to 1.85:1**. Close-up: the curtain fabric **already has a matching hole**. She pushes a finger through it. The thin cold beam of light is born. · ~16 s
  - DAO: **"ม่านก็มีรู..."** (The curtain has a hole too...)
  - DAO: **"แปลว่าตอนที่ปืนลั่น ม่านจะปิดอยู่"** (That means when the gun goes off, the curtains will be closed.)
  - DAO *(turning to them)*: **"เราจะไม่ได้เปิดมันอีกแล้ว"** (We never open them again.)
- **4F** · 3-shot of Martin, Dao and Andy, with Do soft in the background · · ~12 s
  - MARTIN *(phone out)*: **"กูจะโทรหาตำรวจ"** (I'm calling the police.)
  - DAO *(grabbing his wrist)*: **"แล้วจะบอกเขาว่าอะไร ว่าอนาคตทำเลือดกำเดามึงไหลเหรอ"** (And tell them what? That the future gave you a nosebleed?)
  - ANDY: **"ดาวพูดถูก อย่าเพิ่งโทร"** (Dao's right. Don't call yet.)
  - *Do looks from Dao to Andy: why are those two agreeing?*

#### SCENE 5: THE TEST (≈0:25)

- **5A** · Wide, then a close-up on the floor · The vase is **lying on its side on the floor**, though nobody touched it. Dao picks it up and sets it carefully back on the table. Mark the exact floor position: it must match 7B. · ~8 s
  - DAO *(half whisper)*: **"ยังไม่มีใครทำมันตก"** (Nobody's knocked it over yet.)
- **5B** · Close-up, 85 mm, Andy's palm · `hum_4`. A fresh thin cut opens on his palm and blood beads. · ~6 s
  - ANDY *(sitting on his hands)*: **"งั้นกูไม่จับของมีคมแม่งเลย"** (Then I won't touch anything sharp. Nothing.)
- **5C** · Close-up on Martin's wrist · Three scratch lines rise, like fingernails. · 3 s
- **5D** · Slow pan across Andy, then Martin, then Do, landing on Dao · She has no marks at all. · ~6 s
  - DO: **"แล้วทำไมแกไม่มีแผลเลยวะ ดาว"** (So why don't *you* have a mark, Dao?)

#### SCENE 6: THE TRIAL (≈1:15): break the 180° line with a slow 360° orbit around the table

- **6A** · Andy stands at the head of the table, framed slightly low like a judge · · ~8 s
  - ANDY: **"ถ้าจะมีคนยิง ปืนมันต้องอยู่ในห้องนี้ ค้นทุกคน... เริ่มจากมึง โด้"** (If someone's going to shoot, the gun is in this room. We search everyone... starting with you, Do.)
- **6B** · Andy takes Do's phone. Insert: a chat thread "ดาว ❤️" with intimate messages (blurred, but the hearts and the name are readable). · ~16 s
  - DO: **"เอามานี่!"** (Give that back!)
  - MARTIN *(calm, too calm)*: **"ไม่ต้องอ่านหรอก กูรู้แล้ว"** (Don't bother reading it. I already know.)
  - *Close-up on Dao. This hurts more than being caught.*
  - DAO: **"รู้... ตั้งแต่เมื่อไหร่"** (Since... when?)
  - MARTIN: **"เดือนที่แล้ว"** (Last month.)
- **6C** · Do searches Martin's jacket as revenge. Close-up: a **ring box**. He opens it. · ~18 s
  - DO *(cruel laugh)*: **"จะขอแต่งงาน... ในวันเกิดกู ต่อหน้ากูเนี่ยนะ"** (You were going to propose... at my birthday, in front of me?)
  - MARTIN *(to Dao, pleading)*: **"ดาว บอกมันไปเลยว่าเลือกใคร"** (Dao, tell him who you choose.)
  - *Dao opens her mouth, and Do answers first.*
  - DO: **"เขาเลือกกูไปนานแล้ว"** (She chose me a long time ago.)
- **6D** · The orbit continues. Andy tries to sit back down. · ~18 s
  - ANDY: **"กูไว้ทีหลัง"** (Do me last.)
  - DO: **"ไม่ มึงก่อน"** (No. You next.) *He snatches Andy's phone.*
  - *Insert: Do's own messages, "ศุกร์นี้ 800,000 ไม่งั้นกูบอกพ่อมึง" (800,000 by Friday or I tell your dad), then a booking screen for a fictional airline: one-way, departing 07:00 tomorrow.*
  - DO: **"จะหนีเหรอ"** (You were going to run?)
  - ANDY *(flat)*: **"มึงบีบกูเอง"** (You pushed me.)
- **6E** · High angle, wide: three of them closing in on Dao. She clutches the purse. · ~14 s
  - DAO: **"ไม่"** (No.)
  - DAO *(to Andy, the neutral one)*: **"แอนดี้ แกเชื่อเราใช่ไหม"** (Andy, you believe me, right?)
  - ANDY: **"ตอนนี้ไม่มีใครเชื่อใครแล้ว"** (Nobody believes anybody any more.)

### ACT 3: THE GUN

#### SCENE 7: THE GUN (≈0:25)

- **7A** · Andy rips the purse away and the gun slides out onto the white tablecloth. Close-up, 85 mm. · ~10 s
  - DAO: **"เอาไว้ป้องกันตัว"** (It's for protection.)
  - ANDY: **"ป้องกันจากใคร"** (From who?)
  - *Dao looks at Do. Close-up: Do understands.*
- **7B** · Handheld, Dutch tilt · Martin grabs for the gun and Andy grabs his arm. In the scramble **the vase falls and lands exactly in its 5A position** (match the earlier frame). The gun skitters across the floor. · ~6 s
- **7C** · **Floor-level gun shot**, 24 mm, slow push-in, then tilt up to the curtain hole and the pin of light · Everyone frozen. · ~8 s

#### SCENE 8: CLOSING THE LOOP (≈0:30)

- **8A** · Andy dives for the gun, gets it, and aims at the curtain hole with both hands. · ~5 s
  - ANDY: **"ยิงให้มันจบ ๆ ไป"** (Let's just get it over with.)
- **8B** · Do tackles him and they wrestle on the floor. · ~5 s
  - DO: **"ถ้ายิงพลาดล่ะ!"** (What if you miss?!)
- **8C** · **BANG.** Cut to black for 3 frames, then an insert: the curtain twitches and the beam flickers *through* the hole. The bullet passes cleanly through the curtain hole and the window hole. The sound drops to high ringing and muffled breathing for 3 s. · ~6 s
- **8D** · Wide, static · They lie and sit where they are, breathing. Then Dao laughs, a small broken sound, and Martin joins her. · ~14 s
  - DAO: **"จบแล้ว... อันนั้นแหละ"** (It's done... that was it.)
  - MARTIN *(pulling the key from his pocket)*: **"กูจะเปิดประตู ใครอยู่ข้างนอกก็ช่างแม่ง"** (I'm opening the door. I don't care who's out there.)
  - *They move toward the hallway together, almost friends again. Andy drops the gun on the rug as he gets up.*

### ACT 4: NO EXIT (the mattes snap to 1.33:1 on 9A)

#### SCENE 9: THE BODY (≈0:50)

- **9A** · **The hallway frame, exactly matching 0A** · `hum_5`. The ceiling bulb flickers. On the tiles lies **a body, half-covered by the white tablecloth** with its wine stain soaked through with something darker. A hand sticks out from under the cloth, wearing Do's watch and the cuff of a white shirt. · ~8 s
- **9B** · Reverse, 50 mm · Four faces. The living Do steps forward. He doesn't lift the cloth. · ~8 s
  - DO *(barely a sound)*: **"กู... กูยังไม่ตายเลย"** (I... I haven't died yet.)
- **9C** · Close-up on the cloth over the chest: dark around **one small, round hole**. Then a close-up on Dao. · ~6 s
  - DAO: **"มันยังไม่หมด"** (It's not empty.)
- **9D** · All heads turn to the gun on the rug. One second of stillness, then Do dives for it and scrambles back until he hits the table, gun raised and shaking. · ~16 s
  - DO: **"ถอยไป! ทุกคน"** (Stay back! All of you.)
  - ANDY *(reasonable)*: **"โด้ ไม่มีใครอยากจะ—"** (Do, nobody wants to—)
  - DO: **"มึงจะขึ้นเครื่องพรุ่งนี้เช้า แอนดี้"** (You were getting on a plane tomorrow morning, Andy.)
  - DO *(to Martin)*: **"มึงพกแหวนมาวันเกิดกู"** (You brought a ring to my birthday.)
  - DO *(to Dao)*: **"แล้วแก... แกก็พกปืนมา"** (And you... you brought a gun.)
- **9E** · Three 85 mm close-ups · Nobody denies it. Andy closes his fist over the cut on his palm. Martin pulls his sleeve down over the scratches. Dao has no marks, and she is the only one who doesn't look away. · ~10 s

#### SCENE 10: THE ENDING (≈1:05)

- **10A** · Wide down the hallway · Martin walks down the hallway, **steps over the body**, unlocks the front door and opens it a few inches onto darkness. He stands beside it, in the place where Do will die. · ~14 s
  - MARTIN: **"เปิดแล้ว โด้ ไปสิ"** (It's open, Do. Go on.)
- **10B** · Close-up on Do, very long hold · He looks at the open door, then at the hallway he'd have to walk down, past himself. He doesn't move. · ~8 s
- **10C** · Medium · Andy rights a fallen chair, sits at the table and pours the last of the wine into four glasses. · ~12 s
  - ANDY: **"เอาล่ะ..."** *(beat)* **"นั่งกันเถอะ"** (Well... let's sit down.)
- **10D** · Dao sits. Martin walks back, stepping over the body again, and sits. Do stays standing with the gun. · ~10 s
- **10E** · **Overhead table, exactly matching 0B** · The hum returns, nearly the real song now. The lights flicker once. **A new dark-red stain slowly spreads** in the center of the white tablecloth. Do's phone, face up beside the glasses, lights up: a new comment under the grey birthday meme, **"RIP ตำนาน 😂"**. · ~12 s
- **10F** · Slow crane up and away from the overhead: four figures around the table, and at the edge of frame, the shape in the hallway. Fade to black. · ~8 s
- **Credits** · On black: **THE STAIN / รอยเปื้อน**. **The full song plays for the first time.**

---

## 11. Pipeline: phases and checkpoints (cloud edition)

### Repository layout (branch `film`)
```
the-stain/
  FILM_BRIEF.md          ← this file (the user uploaded it)
  PROGRESS.md            ← where we are: phases done, checkpoints approved, decisions, render queue status
  shots.json             ← generated from section 10 (single source of truth)
  assets/  song.wav  characters/  sfx/
  audio/   vo/  hum/  sfx/  mix/
  blender/ set.blend  characters.blend  scenes/<scene>.blend   (keep each file under 90 MB: procedural textures, no huge images)
  scripts/ (all Python, one job per script, re-runnable)
  clips/   <shot>_<chunk>.mp4    ← committed render chunks (CRF 16, H.264)
  checkpoints/                   ← everything the user reviews: PNG/JPG stills, MP3 audio, MP4 under 25 MB
  output/  the_stain_final.mp4  the_stain_th.srt  the_stain_en.srt
  renders/                       ← raw PNG frames, NOT committed (.gitignore)
```

### Session rules
- **Start of every session:** `git fetch`, check out `film`, read `PROGRESS.md`, and confirm the tools still work (`blender -b --version`, `ffmpeg -version`). A new session is a fresh VM, so reinstall anything missing.
- **No job longer than about 20 minutes per command.** Run renders in the background, check on them, and split them into chunks.
- **Commit and push after every finished chunk or step.** Use small, clear commit messages (e.g. `render: 4E chunk 2/3`).
- **Checkpoint delivery:** put review files in `checkpoints/<phase>/`, push, and send the user direct GitHub links on the `film` branch. Video for review at 640×360 or 1280×720, H.264, `-preset veryfast`, under 25 MB. Audio as MP3 at 192 kbps.
- If the repo gets close to GitHub's limits (100 MB per file, a few GB in total), tell the user before going further.

### Phases

**Phase 0: setup check.** Report the Blender version, CPU/RAM/disk, ffmpeg and Python packages. Then run three timing tests and report the numbers:
1. A 1-frame test render of a simple lit room with one stylized figure, at 1280×720, in EEVEE headless and in Cycles CPU (16 and 32 samples, denoised). Decide the engine with the user.
2. One Thai test line with edge-tts (and ElevenLabs if a key exists).
3. Hum generation from the song, using ffmpeg on a 5-second fragment.

Give a **total render-time estimate**: about 8 minutes is about 5,800 unique frames on twos, times the seconds per frame. Then ask the user, in one message: (1) the engine choice given the timings, (2) Option A or B characters (default B), (3) edge-tts or ElevenLabs, (4) whether to keep the full 8–10 minute length or start with a shorter first cut (for example Scenes 0–3 only). Commit test images to `checkpoints/phase0/`.

**Phase 1: script → `shots.json` → voices.** Parse section 10 into `shots.json` (shot id, scene, act, camera, lens, framing, action, characters, lines, pauses, matte ratio, lighting state, hum file, continuity notes). Generate all Thai voice lines in batches and the 5 hum versions. Build a **radio-play cut** (voices, hum and sound effects over black, with the written pauses) so the whole film's timing can be heard. **CHECKPOINT 1:** `checkpoints/phase1/radio_play.mp3`, plus a 1-minute sample with one line per character. The user checks pronunciation and casting.

**Phase 2: set and look development.** Build the set at real scale. Light all 3 lighting states. Render 6 stills at 1280×720: Act 1 wide, Act 2 after the curtains close (with the pin beam), Act 4 top-light close-up, the hallway frame empty and with the body, and the overhead table. **CHECKPOINT 2.**

**Phase 3: characters.** Build (Option B) or import (Option A), then style, rig and lip-sync-test one line per character. Commit a 4-view turnaround still of each and one 5-second talking test MP4. **CHECKPOINT 3.**

**Phase 4: animatic.** Block every shot with the final cameras and the timing from Phase 1 audio. Use rough poses at 640×360, Workbench or Cycles at 4 samples. Render it scene by scene in chunks, then edit it with ffmpeg into one video with the full audio. **CHECKPOINT 4:** the most important review, because it checks story, pacing and angles before the expensive renders. If it's over 25 MB, split it by act.

**Phase 5: final render, chunked and resumable.**
- Render queue in `PROGRESS.md`: every shot split into chunks of about 60–120 **unique** frames, each sized to finish in under 20 minutes at the measured speed.
- For each chunk: render the PNGs to `renders/` (skipping existing frames), look at one frame, encode to `clips/<shot>_<chunk>.mp4` (CRF 16, doubling frames for the on-twos look), delete the PNGs, then commit, push and tick it off in `PROGRESS.md`.
- Check the matching shots (0A/9A, 0B/10E, 5A/7B) and the continuity table before each scene.
- **CHECKPOINT 5** after Scene 1 is fully rendered: commit `checkpoints/phase5/scene1.mp4`. After approval, the user may run **Prompt 3** (Part B) so rendering continues on a schedule.

**Phase 6: finishing.** Join all clips. In ffmpeg, or a Blender compositor pass per clip if needed: aspect mattes, light film grain, subtle vignette and a slight color grade per act (Act 1 warm, Act 2 neutral and desaturating, Act 4 cold and green-tinged). Final mix to about −14 LUFS. Make Thai and English `.srt` files from `shots.json`, plus one version with burned-in Thai subtitles (Noto Sans Thai). Export H.264 MP4 (`-preset slow`, CRF 18) to `output/`. If the final file is over 100 MB, also make a smaller phone version and tell the user how to download the full one (for example as a GitHub release asset, if possible here). **FINAL CHECKPOINT.**

---

## 12. Quality rules

- **Look at what you render.** After every still or preview, open the image and check it against this brief: framing, lighting state, continuity and color. Don't assume a render is right because it finished.
- Faces and eyes must be readable in every close-up. If the top light hides the eyes too much, add a faint eye-light (a tiny catch light) rather than flattening the lighting.
- The cuts follow the dialogue: cut on the line or the look, never in the middle of a word.
- Keep the violence stylized: impacts are cuts and sound, never gore.
- Scripts must be re-runnable and idempotent, so one shot can be re-rendered without breaking the others.
- When something fails or looks wrong, fix the cause and say what changed. Don't quietly lower the bar.
