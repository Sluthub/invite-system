<template>
    <div class="flex flex-col justify-center items-center space-y-4">
        <div class="text-center">
            <!-- Title -->
            <h1 class="text-2xl font-semibold">
                {{ __('Welcome to the Sluthub invites System') }}
            </h1>

            <!-- Subtitle -->
            <div class="text-gray-500 dark:text-gray-400">
                <h2 class="text-xs">
                    Automatic User Invitation System for Sluthub
                </h2>
            </div>

            <hr class="my-4 border-gray-200 dark:border-gray-700" />

            <!-- Description -->
            <p class="text-base text-center">
                Sluthub is your favorite Media Server. Allowing you
                to watch any Movie, TV show or Anime you want, whenever
                you wish to do so. No strings attached. You can even
                request new titles to be added!
            </p>
        </div>
    </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
    name: 'WelcomeView',
});
</script>
