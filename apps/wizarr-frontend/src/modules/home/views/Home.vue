<template>
    <DefaultNavBar :button="isAuthenticated ? 'Admin Dashboard' : 'Admin Login'" :buttonLink="isAuthenticated ? '/admin' : '/login'" />

        <!-- Hero Section -->
        <section class="bg-gray-100 dark:bg-gray-900 px-2 md:px-4 lg:px-6 xl:px-8 mt-28 md:mt-0">
            <div class="py-8 px-4 mx-auto max-w-screen-xl text-center lg:py-16">
                <h1 class="mb-4 text-4xl font-extrabold tracking-tight leading-none text-gray-900 md:text-5xl lg:text-6xl dark:text-white">{{ __("Welcome to") }} The Screening Room</h1>
                <p class="mb-8 text-lg font-normal text-gray-500 sm:px-16 lg:px-48 dark:text-gray-400">
                    {{ __("The Screening Room is your favorite Media Server. Allowing you to watch any Movie, TV show or Anime you want, whenever you wish to do so. No strings attached. You can even request new titles to be added!") }}
                </p>

                <p class="mb-8 text-sm font-bold text-gray-500 sm:px-16 lg:px-48 dark:text-gray-400">
                    {{ __("If you were sent here by a friend, please request access or if you have an invite code, please click Get started!") }}
                </p>
                <div class="flex flex-col space-y-2 sm:flex-row sm:justify-center sm:space-y-0 sm:space-x-3">
                    <FormKit type="button" @click="$router.push('/join')" theme="primary" suffix-icon="fas fa-arrow-right">{{ __("Get Started") }}</FormKit>
                    <span class="inline-flex items-center text-gray-500 dark:text-gray-400 justify-center"> or </span>
                    <FormKit type="button" :disabled="true" data-theme="transparent">{{ __("Request Access") }}</FormKit>
                </div>
            </div>
        </section>
        <div class="flex justify-center items-center flex-col mb-3 space-y-6">
            <p class="text-sm text-center text-gray-900 dark:text-white">
                {{ __('Made with ❤️ by') }}
                <a
                    class="text-primary font-bold hover:underline"
                    target="_blank"
                    href="https://github.com/wizarrrr/wizarr"
                >
                    Wizarr
                </a>
            </p>
        </div>
    </div>
</template>

<script lang="ts">
import { mapActions, mapState } from 'pinia';
import { defineComponent } from 'vue';
import { useAuthStore } from "@/stores/auth";
import { useServerStore } from '@/stores/server';
import { Collapse } from 'vue-collapsed';

import Carousel from '../../core/components/Carousel.vue';
import WizarrLogo from '@/components/WizarrLogo.vue';

import DefaultNavBar from "@/components/NavBars/DefaultNavBar.vue";

import eventBus from '../events';

import type { Socket } from 'socket.io-client';
import type {
    ServerToClientEvents,
    ClientToServerEvents,
} from '@/plugins/socket';
import type { EventRecords } from '../types/EventRecords';

export default defineComponent({
    name: 'HomeView',
    components: {
        DefaultNavBar,
        WizarrLogo,
        Carousel,
        Collapse,
    },
    data() {
        return {
            socket: null as Socket<
                ServerToClientEvents,
                ClientToServerEvents
            > | null,
            eventBus: eventBus,
            pleaseWait: true,
            pageTitle: '',
            currentView: 1,
            activeStep: 0,
            views: [
                {
                    name: 'home',
                    title: this.__('Please enter your invite code:'),
                    component: () => import('../pages/JoinForm.vue'),
                },
                // {
                //     name: "payment",
                //     title: this.__("Make Payment"),
                //     component: () => import("../pages/Payment.vue"),
                //     props: {
                //         eventBus: eventBus,
                //         code: this.$route.params.invite as string,
                //     },
                // },
                {
                    name: 'create',
                    title: this.__('Setup your account'),
                    component: () => import('../pages/Signup.vue'),
                    props: {
                        eventBus: eventBus,
                    },
                },
                {
                    name: 'stepper',
                    title: this.__('Please wait...'),
                    component: () => import('../pages/Stepper.vue'),
                    props: {
                        eventBus: eventBus,
                    },
                },
                {
                    name: 'success',
                    title: this.__('All done!'),
                    component: () => import('../pages/Complete.vue'),
                },
                {
                    name: 'error',
                    component: () => import('../pages/Error.vue'),
                    props: {
                        title: this.__('Uh oh!'),
                        message: this.__(
                            'Something went wrong while trying to join the server. Please try again later.',
                        ),
                    },
                },
            ],
        };
    },
    computed: {
        noHeader() {
            return this.isView(['error']);
        },
        ...mapState(useServerStore, ['settings']),
        ...mapActions(useAuthStore, ["isAuthenticated"]),
    },
    methods: {
        isView(name: string | string[]) {
            return Array.isArray(name)
                ? name.includes(this.views[this.currentView - 1].name)
                : this.views[this.currentView - 1].name == name;
        },
        async showError(title: string, message: string) {
            // Hide the please wait screen
            this.pleaseWait = false;

            // Change the error screen props
            this.views[this.currentView - 1].props = {
                title: title,
                message: message,
            };

            // Show the error screen
            this.currentView =
                this.views.findIndex((view) => view.name == 'error') + 1;
        },
        async connected() {
            // Check for a socket id
            if (this.socket?.id == undefined) {
                this.showError(
                    this.__('Uh oh!'),
                    this.__('Could not connect to the server.'),
                );
            }

            this.pleaseWait = false;
        },
        async plexCreateAccount(value: EventRecords['plexCreateAccount']) {
            // Create the form data
            const formData = new FormData();
            formData.append('token', value);
            formData.append('code', this.$route.params.invite as string);
            formData.append('socket_id', this.socket?.id as string);

            // Make API request to create the account
            const response = await this.$axios
                .post('/api/plex', formData)
                .catch((err) => {
                    this.showError(
                        this.__('Uh oh!'),
                        err.response?.data?.message ??
                            this.__('Could not create the account.'),
                    );
                });

            // Check that response contains a room
            if (response?.data?.room == undefined) {
                this.showError(
                    this.__('Uh oh!'),
                    this.__('Could not create the account.'),
                );
            }

            // Show the next screen
            this.currentView =
                this.views.findIndex((view) => view.name == 'stepper') + 1;
        },
        async jellyfinCreateAccount(
            value: EventRecords['jellyfinCreateAccount'],
        ) {
            // Create the form data
            const formData = new FormData();
            formData.append('username', value.username);
            formData.append('email', value.email);
            formData.append('password', value.password);
            formData.append('code', this.$route.params.invite as string);
            formData.append('socket_id', this.socket?.id as string);

            // Make API request to create the account
            const response = await this.$axios
                .post('/api/jellyfin', formData)
                .catch((err) => {
                    this.showError(
                        this.__('Uh oh!'),
                        err.response?.data?.message ??
                            this.__('Could not create the account.'),
                    );
                });

            // Check that response contains a room
            if (response?.data?.room == undefined) {
                this.showError(
                    this.__('Uh oh!'),
                    this.__('Could not create the account.'),
                );
            }

            // Show the next screen
            this.currentView =
                this.views.findIndex((view) => view.name == 'stepper') + 1;
        },
        async embyCreateAccount(
            value: EventRecords['embyCreateAccount'],
        ) {
            // Create the form data
            const formData = new FormData();
            formData.append('username', value.username);
            formData.append('email', value.email);
            formData.append('password', value.password);
            formData.append('code', this.$route.params.invite as string);
            formData.append('socket_id', this.socket?.id as string);

            // Make API request to create the account
            const response = await this.$axios
                .post('/api/emby', formData)
                .catch((err) => {
                    this.showError(
                        this.__('Uh oh!'),
                        err.response?.data?.message ??
                            this.__('Could not create the account.'),
                    );
                });

            // Check that response contains a room
            if (response?.data?.room == undefined) {
                this.showError(
                    this.__('Uh oh!'),
                    this.__('Could not create the account.'),
                );
            }

            // Show the next screen
            this.currentView =
                this.views.findIndex((view) => view.name == 'stepper') + 1;
        },
    },
    async mounted() {
        // Initialize the socket connection
        this.socket = this.$io('/' + this.settings.server_type);
        this.socket.on('connect', () => this.connected());
        this.socket.on('connect_error', () =>
            this.showError(
                this.__('Uh oh!'),
                this.__('Could not connect to the server.'),
            ),
        );
        this.socket.on('error', (message) =>
            this.showError(this.__('Uh oh!'), message),
        );
        this.socket.on('error', this.$toast.error);
        this.socket.on('log', (message) => console.error(message));
        this.socket.on('message', this.$toast.info);
        this.socket.on('step', (step: number) => (this.activeStep = step));
        this.socket.on('done', () =>
            setTimeout(
                () =>
                    (this.currentView =
                        this.views.findIndex((view) => view.name == 'success') +
                        1),
                1000,
            ),
        );

        // Initialize the event bus
        this.eventBus.on('plexCreateAccount', this.plexCreateAccount);
        this.eventBus.on('jellyfinCreateAccount', this.jellyfinCreateAccount);
        this.eventBus.on('embyCreateAccount', this.embyCreateAccount);

        this.eventBus.on(
            'pleaseWait',
            (pleaseWait) => (this.pleaseWait = pleaseWait),
        );
        this.eventBus.on('pageTitle', (title) => (this.pageTitle = title));
    },
    async beforeUnmount() {
        // Disconnect the socket
        this.socket?.disconnect();

        // Remove the event bus listeners
        this.eventBus.off('*');
    },
});
</script>
