<script setup lang="ts">
import { ref } from "vue";
import {
  ArrowNarrowRightIcon,
  ArrowNarrowDownIcon,
} from "@heroicons/vue/solid";

const props = defineProps<{
  clueNumber: number;
  blocked: boolean;
  borderTop: boolean;
  borderRight: boolean;
  borderDown: boolean;
  borderLeft: boolean;
  arrowRight: boolean;
  arrowDown: boolean;
  active: boolean;
  squareLetter: string;
  displayLetter: boolean;
}>();

const count = ref(0);
</script>

<template>
  <div
    :class="[
      props.active
        ? 'bg-indigo-200'
        : props.clueNumber > 0 || props.blocked
        ? 'bg-indigo-700'
        : '',
      props.borderTop ? 'border-t-2' : 'border-t-0',
      props.borderRight ? 'border-r-2' : 'border-r-0',
      props.borderDown ? 'border-b-2' : 'border-b-0',
      props.borderLeft ? 'border-l-2' : 'border-l-0',
    ]"
    class="
      flex
      place-content-center
      h-[0.9cm]
      w-[0.9cm]
      border-indigo-700
      text-indigo-700
      relative
    "
  >
    <p
      v-if="displayLetter && squareLetter !== '' && squareLetter !== ' '"
      class="
        leading-[0.8cm]
        text-indigo-700
        tracking-normal
        w-full
        font-mono
        text-center
      "
    >
      {{ squareLetter }}
    </p>
    <p
      v-if="props.clueNumber > 0"
      class="
        leading-[0.8cm]
        text-white
        tracking-normal
        w-full
        font-mono
        text-center
      "
    >
      {{ clueNumber }}
    </p>
    <ArrowNarrowRightIcon
      v-if="props.arrowRight"
      class="absolute -right-[14px] top-[9px] w-[4mm]"
    ></ArrowNarrowRightIcon>
    <ArrowNarrowDownIcon
      v-if="props.arrowDown"
      class="absolute -bottom-[14px] left-[9px] w-[4mm]"
    />
  </div>
</template>
