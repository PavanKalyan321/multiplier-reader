# Architecture & System Design

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      GAME SCREEN                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  MULTIPLIER VALUE                                    │  │
│  │  5.23x                                               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    SCREEN CAPTURE                            │
│   (Full screen → Region extraction → Preprocessing)         │
│                   [screen_capture.py]                       │
└─────────────────────────────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   OCR EXTRACTION                             │
│   (Tesseract → Regex parsing → Multiplier extraction)       │
│                [multiplier_reader.py]                       │
└─────────────────────────────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  STATE TRACKING                              │
│   (Event detection → Status classification)                 │
│                 [game_tracker.py]                           │
└─────────────────────────────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│               OUTPUT & STATISTICS                            │
│   (Logging → Console output → Statistics)                   │
│                    [main.py]                                │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow Pipeline

```
Input: Screen Pixels
  ↓
[ScreenCapture]
  • ImageGrab.grab() - Full screen capture
  • Crop to region - Extract region of interest
  • cv2.cvtColor() - Convert to BGR
  ↓
[Preprocessing]
  • cv2.cvtColor(BGR→Gray) - Convert to grayscale
  • CLAHE - Enhance contrast
  • cv2.threshold() - Binary conversion
  • Morphology - Denoise
  ↓
[MultiplierReader]
  • pytesseract.image_to_string() - OCR
  • re.findall() - Extract numbers
  • Float conversion - Parse multiplier
  ↓
[GameTracker]
  • Compare with previous value
  • Detect status transitions
  • Generate events
  • Update statistics
  ↓
[Output]
  • Console logging
  • Statistics display
  • Configuration save
  ↓
Output: Game Events & Multiplier Value
```

## Module Interaction Map

```
┌────────────────────────────────────────────────────────────┐
│                        main.py                              │
│  Orchestrates the entire monitoring pipeline               │
├────────────────────────────────────────────────────────────┤
│ Uses:                                                       │
│  • ScreenCapture - for screen data                         │
│  • MultiplierReader - for OCR                              │
│  • GameTracker - for event detection                       │
│  • config - for region loading                             │
└────────────────────────────────────────────────────────────┘
           ▲              ▲              ▲
           │              │              │
           │              │              │
    ┌──────┴─────┐  ┌────┴──────┐  ┌───┴───────────┐
    │             │  │            │  │               │
┌───┴──────┐ ┌───┴──────┐ ┌──────┴───┐ ┌─────────────┴──┐
│ screen   │ │multiplier│ │ game     │ │ config.py    │
│ capture  │ │ reader   │ │ tracker  │ │              │
├──────────┤ ├──────────┤ ├──────────┤ ├──────────────┤
│ Manages: │ │ Manages: │ │ Manages: │ │ Manages:     │
│ • PIL    │ │ • OCR    │ │ • Events │ │ • Region     │
│ • OpenCV │ │ • Regex  │ │ • State  │ │ • Config     │
│ • Image  │ │ • Number │ │ • Status │ │ • Save/Load  │
│   proc   │ │   parsing│ │ • History│ │              │
└──────────┘ └──────────┘ └──────────┘ └──────────────┘
```

## State Machine

```
┌─────────────────────────────────────────────────────────────┐
│ GAME STATE MACHINE                                           │
└─────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │    IDLE      │
                    │ is_running=F │
                    │ crashed=F    │
                    └──────┬───────┘
                           │ multiplier = 1.0x
                           ▼
                    ┌──────────────┐
                    │  STARTING    │
                    │ is_running=T │
    ┌──────────────┤ crashed=F    │◄──────────┐
    │              └──────┬───────┘           │ multiplier > 1
    │                     │ multiplier > 1    │ but < 10
    │                     ▼                   │
    │ multiplier ┌──────────────┐            │
    │    = 0     │  RUNNING     │────────────┘
    │            │ is_running=T │
    │            │ crashed=F    │
    │            └──────┬───────┘
    │                   │ multiplier >= 10
    │                   ▼
    │            ┌──────────────┐
    │            │     HIGH     │
    │            │ is_running=T │
    │            │ crashed=F    │
    │            └──────┬───────┘
    │                   │ multiplier <= 0.5
    │                   ▼
    │            ┌──────────────┐
    └───────────►│   CRASHED    │
                 │ is_running=F │
                 │ crashed=T    │
                 └──────────────┘
```

## Event Timeline Example

```
Time  │ Event                │ Multiplier │ Status    │ Duration
──────┼──────────────────────┼────────────┼───────────┼──────────
00.0s │ GAME_START           │ 1.00x      │ STARTING  │ 0s
00.5s │ MULTIPLIER_INCREASE  │ 1.50x      │ RUNNING   │ 0.5s
01.0s │ MULTIPLIER_INCREASE  │ 2.25x      │ RUNNING   │ 1.0s
01.5s │ MULTIPLIER_INCREASE  │ 3.50x      │ RUNNING   │ 1.5s
02.0s │ MULTIPLIER_INCREASE  │ 5.25x      │ RUNNING   │ 2.0s
02.5s │ MULTIPLIER_INCREASE  │ 7.50x      │ RUNNING   │ 2.5s
03.0s │ MULTIPLIER_INCREASE  │ 10.00x     │ HIGH      │ 3.0s
03.5s │ HIGH_MULTIPLIER      │ 10.00x     │ HIGH      │ 3.5s
04.0s │ MULTIPLIER_INCREASE  │ 15.50x     │ HIGH      │ 4.0s
04.5s │ MULTIPLIER_INCREASE  │ 23.75x     │ HIGH      │ 4.5s
05.0s │ CRASH                │ 0.00x      │ CRASHED   │ 5.0s (final)
```

## Class Structure

### ScreenCapture
```
ScreenCapture
├── region: RegionConfig
├── last_frame: np.ndarray
│
├── capture_full_screen() → np.ndarray
├── capture_region() → np.ndarray
├── preprocess_image(image) → np.ndarray
├── detect_changes(new_frame) → (bool, float)
└── save_debug_frame(image, filename)
```

### MultiplierReader
```
MultiplierReader
├── screen_capture: ScreenCapture
├── last_multiplier: float
│
├── read_multiplier() → float
├── extract_multiplier(image) → float
├── get_multiplier_with_status() → dict
├── _detect_status(multiplier) → str
└── _get_status_message(status) → str
```

### GameTracker
```
GameTracker
├── state: GameState
├── events: List[GameEvent]
├── previous_multiplier: float
├── crash_threshold: float
│
├── update(multiplier, status) → List[GameEvent]
├── get_round_summary() → dict
└── get_event_history(limit) → List[GameEvent]
```

### MultiplierReaderApp
```
MultiplierReaderApp
├── region: RegionConfig
├── screen_capture: ScreenCapture
├── multiplier_reader: MultiplierReader
├── game_tracker: GameTracker
├── stats: dict
│
├── run()
├── update_step()
├── log(message)
├── log_event(event)
├── print_status(...)
└── print_stats()
```

## Performance Characteristics

```
Update Cycle Timing (default 0.5s interval):

0ms     ┬─ Main loop starts
        │
1ms     ├─ ScreenCapture.capture_full_screen()
        │   └─ PIL.ImageGrab() ~1ms
        │   └─ cv2.cvtColor() ~0.5ms
        │
3ms     ├─ ScreenCapture.capture_region()
        │   └─ Array slicing ~0.1ms
        │
4ms     ├─ ScreenCapture.preprocess_image()
        │   └─ Grayscale ~0.5ms
        │   └─ CLAHE ~1ms
        │   └─ Threshold ~0.5ms
        │   └─ Morphology ~1ms
        │
7ms     ├─ MultiplierReader.extract_multiplier()
        │   └─ pytesseract.image_to_string() ~50-100ms
        │   └─ Regex parsing ~0.1ms
        │
110ms   ├─ GameTracker.update()
        │   └─ Status detection ~0.1ms
        │   └─ Event generation ~0.1ms
        │
111ms   ├─ Statistics update
        │
112ms   ├─ Console output
        │
120ms   ├─ Sleep (0.5s - 0.12s = 0.38s)
        │
500ms   └─ Next cycle
```

## Configuration Flow

```
┌──────────────────────────────────────────────────────────┐
│          gui_selector.py                                 │
│   (User selects region visually)                         │
└─────────────────────┬──────────────────────────────────┘
                      │ User clicks "Save Region"
                      ▼
              ┌────────────────────┐
              │ RegionConfig       │
              │ x1, y1, x2, y2     │
              └────────────┬───────┘
                           │ save_config()
                           ▼
                 ┌──────────────────────┐
                 │ multiplier_config    │
                 │ .json file           │
                 └──────────┬───────────┘
                            │ load_config()
                            ▼
                  ┌──────────────────────┐
                  │ ScreenCapture        │
                  │ region parameter     │
                  └──────────────────────┘
```

## Error Handling Flow

```
Multiplier Read Attempt
        │
        ▼
    ┌───────────────────────┐
    │ Capture succeeded?    │
    └───┬─────────────┬─────┘
        │ YES         │ NO
        ▼             ▼
      Preprocess  Return None
        │         (ERROR status)
        ▼
    ┌───────────────────────┐
    │ OCR succeeded?        │
    └───┬─────────────┬─────┘
        │ YES         │ NO
        ▼             ▼
     Parse       Return None
      Regex      (ERROR status)
        │
        ▼
    ┌───────────────────────┐
    │ Number found?         │
    └───┬─────────────┬─────┘
        │ YES         │ NO
        ▼             ▼
     Return      Return None
     Float       (ERROR status)
```

---

This architecture provides:
- ✅ Separation of concerns
- ✅ Easy to test individual components
- ✅ Scalable and maintainable code
- ✅ Clear data flow
- ✅ Robust error handling
