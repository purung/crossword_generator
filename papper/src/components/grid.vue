<template>
  <div class="mt-12">
    <div v-if="displayGrid" class="flex place-content-center mt-12">
      <div class="max-w-[21cm] grid grid-cols-21 auto-cols-min gap-0">
        <Square
          v-for="sq in squares"
          :key="sq.key"
          :clue-number="sq.clueNumber"
          :blocked="sq.blocked"
          :arrow-down="sq.arrowDown"
          :arrow-right="sq.arrowRight"
          :border-down="sq.borderBottom"
          :border-right="sq.borderRight"
          :border-left="sq.borderLeft"
          :border-top="sq.borderTop"
          :active="activeSquare == sq.key"
          :square-letter="sq.letter"
          :display-letter="displayLetters"
        />
      </div>
    </div>
    <div
      v-if="displayClues"
      class="grid grid-cols-2 font-serif text-xs place-content-center mx-auto"
    >
      <div>
        <h1 class="text-red-700 italic text-2xl mb-3 text-center">
          Horisontellt
        </h1>
        <div class="columns-2 gap-3">
          <p v-for="sq in horizontalClues" :key="sq.clueNumber">
            <span class="text-red-700 font-semibold">
              {{ sq.clueNumber }}.
            </span>
            {{ sq.horizonalClue }}
          </p>
        </div>
      </div>
      <div>
        <h1 class="text-red-700 italic text-2xl mb-3 text-center">Vertikalt</h1>
        <div class="columns-2 gap-3">
          <p v-for="sq in verticalClues" :key="sq.clueNumber">
            <span class="text-red-700 font-semibold">
              {{ sq.clueNumber }}.
            </span>
            {{ sq.verticalClue }}
          </p>
        </div>
      </div>
    </div>
    <div class="print:hidden fixed left-5 top-5 p-5">
      <p>Rad: {{ currentRow }}</p>
      <p>Ruta: {{ currentColumn }}</p>
      <p>Box: {{ activeSquare }}</p>
    </div>
    <Dialog :open="clueInputOpen" as="div" class="z-50">
      <div class="fixed inset-0 bg-white bg-opacity-90 z-101 overflow-y-auto">
        <div class="min-h-screen px-4 text-center">
          <DialogOverlay class="fixed inset-0" />
          <div
            class="
              inline-block
              w-full
              max-w-lg
              p-12
              z-101
              my-16
              overflow-hidden
              text-left
              align-middle
              bg-slate-100
              shadow-xl
            "
          >
            <DialogTitle class="text-red-700 text-2xl mb-6"
              >Ledtrådar</DialogTitle
            >
            <input
              @keyup.stop
              :disabled="!acceptInput"
              v-model="horizonalClue"
              class="
                w-full
                block
                py-2
                my-4
                px-4
                rounded-3xl
                border-gray-400
                focus:border-none
                focus:ring-1
                focus:ring-red-700
                focus:ring-opacity-80
                outline-none
              "
            />
            <input
              v-model="verticalClue"
              @keyup.stop
              :disabled="!acceptInput"
              class="
                w-full
                block
                py-2
                my-4
                px-4
                rounded-3xl
                border-gray-400
                focus:border-none
                focus:ring-1
                focus:ring-red-700
                focus:ring-opacity-80
                outline-none
              "
            />
            <button
              v-if="inputMode === 'letters'"
              class="
                bg-red-700
                rounded-3xl
                text-white
                py-2
                px-6
                mt-6
                font-mono font-semibold
                text-center
              "
              @click="updateLetters"
            >
              OK
            </button>
            <button
              v-if="inputMode === 'clue'"
              class="
                bg-red-700
                rounded-3xl
                text-white
                py-2
                px-6
                mt-6
                font-mono font-semibold
                text-center
              "
              @click="updateClue"
            >
              OK
            </button>
          </div>
        </div>
      </div>
    </Dialog>
  </div>
</template>
<script setup lang="ts">
import { computed, reactive, ref } from "@vue/reactivity";
import Square from "./square.vue";
import tinykeys from "tinykeys";
import { Dialog, DialogOverlay, DialogTitle } from "@headlessui/vue";

const gridColumns = 21;
const gridRows = 21;
const squareCount = gridColumns * gridRows;

const _squares = [...Array(squareCount).keys()].map((x) => {
  return {
    key: x,
    clueNumber: 0,
    blocked: false,
    borderTop: false,
    borderRight: true,
    borderBottom: true,
    borderLeft: false,
    arrowRight: false,
    arrowDown: false,
    active: false,
    horizonalClue: "",
    verticalClue: "",
    letter: "",
  };
});
let squares = reactive(_squares);

const activeSquare = ref(0);
const horizonalClue = ref("");
const verticalClue = ref("");
const clueInputOpen = ref(false);
const displayGrid = ref(true);
const displayClues = ref(true);
const displayLetters = ref(true);
const acceptInput = ref(false);
const inputMode = ref("clue");

const rowFrom = (coordinate: number) => {
  return Math.floor(coordinate / gridColumns);
};
const columnFrom = (coordinate: number) => {
  return coordinate - rowFrom(coordinate) * gridColumns;
};
const horizontalPath = (coordinate: number, length: number) => {
  const limit = coordinate + length;
  return squares.filter((_sq, ix) => ix >= coordinate && ix <= limit);
};
const verticalPath = (coordinate: number, length: number) => {
  const limit = coordinate + length;
  const skips = [...Array(length).keys()]
    .map((sk) => sk + 1)
    .map((sk) => coordinate + sk * gridColumns);
  return [
    squares[coordinate],
    ...squares.filter((_sq, ix) => skips.includes(ix)),
  ];
};

const latestClueNumber = computed(() => {
  return Math.max(...squares.map((sq) => sq.clueNumber));
});
const horizontalClues = computed(() => {
  return squares.filter((s) => s.clueNumber > 0 && s.horizonalClue !== "");
});
const verticalClues = computed(() => {
  return squares.filter((s) => s.clueNumber > 0 && s.verticalClue !== "");
});
const currentRow = computed(() => {
  return rowFrom(activeSquare.value);
});
const currentColumn = computed(() => {
  return columnFrom(activeSquare.value);
});

const setLetters = (letters: string, origo: number, vertical: boolean) => {
  const length = letters.length;
  if (vertical) {
    const path = verticalPath(origo, length);
    Array.from(letters).forEach((ltr, ix) => {
      path[ix].letter = ltr.toUpperCase();
    });
  } else {
    const path = horizontalPath(origo, length);
    Array.from(letters).forEach((ltr, ix) => {
      path[ix].letter = ltr.toUpperCase();
    });
  }
};

const updateClue = () => {
  squares[activeSquare.value].horizonalClue = horizonalClue.value;
  squares[activeSquare.value].verticalClue = verticalClue.value;
  clueInputOpen.value = false;
  acceptInput.value = false;
};
const updateLetters = () => {
  if (verticalClue.value !== "") {
    setLetters(verticalClue.value, activeSquare.value, true);
  }
  if (horizonalClue.value !== "") {
    setLetters(horizonalClue.value, activeSquare.value, false);
  }
  clueInputOpen.value = false;
  acceptInput.value = false;
};
tinykeys(
  window,
  {
    "Shift+U": () => {
      inputMode.value = "clue";
      horizonalClue.value = squares[activeSquare.value].horizonalClue;
      verticalClue.value = squares[activeSquare.value].verticalClue;
      clueInputOpen.value = true;
      acceptInput.value = true;
    },
    "Shift+Y": () => {
      inputMode.value = "letters";
      horizonalClue.value = "";
      verticalClue.value = "";
      clueInputOpen.value = true;
      acceptInput.value = true;
    },
    KeyJ: () => {
      const newValue = activeSquare.value + gridColumns;
      if (newValue > squareCount - 1) {
        activeSquare.value = newValue - squareCount;
      } else {
        activeSquare.value = newValue;
      }
    },
    KeyK: () => {
      const newValue = activeSquare.value - gridColumns;
      if (newValue < 0) {
        activeSquare.value = squareCount + newValue;
      } else {
        activeSquare.value = newValue;
      }
    },
    KeyL: () => {
      const newValue = activeSquare.value + 1;
      if (newValue >= squareCount) {
        activeSquare.value = 0;
      } else {
        activeSquare.value = newValue;
      }
    },
    KeyH: () => {
      const newValue = activeSquare.value - 1;
      if (newValue < 0) {
        activeSquare.value = squareCount + newValue;
      } else {
        activeSquare.value = newValue;
      }
    },
    Digit0: () => {
      activeSquare.value = -1;
    },
    KeyF: () => {
      displayClues.value = !displayClues.value;
    },
    KeyG: () => {
      displayGrid.value = !displayGrid.value;
    },
    KeyD: () => {
      displayLetters.value = !displayLetters.value;
    },
    KeyC: () => {
      const newClue = latestClueNumber.value + 1;
      squares[activeSquare.value].clueNumber = newClue;
    },
    KeyV: () => {
      const active = squares[activeSquare.value].clueNumber;
      squares.forEach((sq) => {
        if (sq.clueNumber > active) {
          sq.clueNumber -= 1;
        } else if (sq.clueNumber === active) {
          sq.clueNumber = 0;
        }
      });
    },
    KeyQ: () => {
      squares[activeSquare.value].borderTop =
        !squares[activeSquare.value].borderTop;
    },
    KeyX: () => {
      squares[activeSquare.value].blocked =
        !squares[activeSquare.value].blocked;
    },
    KeyW: () => {
      squares[activeSquare.value].borderRight =
        !squares[activeSquare.value].borderRight;
    },
    KeyE: () => {
      squares[activeSquare.value].borderBottom =
        !squares[activeSquare.value].borderBottom;
    },
    KeyR: () => {
      squares[activeSquare.value].borderLeft =
        !squares[activeSquare.value].borderLeft;
    },
    KeyO: () => {
      squares[activeSquare.value].arrowRight =
        !squares[activeSquare.value].arrowRight;
    },
    KeyP: () => {
      squares[activeSquare.value].arrowDown =
        !squares[activeSquare.value].arrowDown;
    },
    "Control+Alt+S": () => {
      const json = JSON.stringify(squares);
      localStorage.setItem("korsord", json);
    },
    "Control+Alt+O": () => {
      const json = localStorage.getItem("korsord");
      if (json !== null) {
        squares.splice(0, squares.length, ...JSON.parse(json));
      }
    },
  },
  { event: "keyup" }
);
</script>
