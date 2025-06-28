// js/app.js
(function () {
    'use strict';

    angular
        .module('arztPortalApp', ['ngRoute'])
        .factory('ApiService', ApiService)
        .config(routeConfig)
        .controller('NavController', NavController)
        .controller('HomeController', HomeController)
        .controller('KalenderController', KalenderController)
        .controller('ProtokolleController', ProtokolleController)
        .controller('ProfileController', ProfileController);

    // ===== ApiService: Kommunikation mit Backend =====
    ApiService.$inject = ['$http'];
    function ApiService($http) {
        const baseUrl = 'http://34.217.126.24/';


        return {
            // USER
            updateUserProfile: (user) => $http.put(baseUrl + 'update_profile', {
                user_id: user.id || 'demo-user-id',
                first_name: user.vorname,
                surname: user.nachname,
                birth_date: user.geburtsdatum,
                insurance: user.versicherung
            }),

            // DOCTOR
            listDoctors: () => $http.get(baseUrl + 'list_all_doctors'),
            addDoctor: (doc) => $http.post(baseUrl + 'add_doctor', {
                name: doc.name,
                phone: doc.telefon,
                opening_hours: doc.oeffnungszeiten,
                profession: doc.fachrichtung
            }),
            updateDoctor: (doc) => $http.put(baseUrl + 'update_doctor', {
                doctor_id: doc.doctor_id,
                name: doc.name,
                phone: doc.telefon,
                opening_hours: doc.oeffnungszeiten,
                profession: doc.fachrichtung
            }),
            deleteDoctor: (id) => $http.delete(baseUrl + 'delete_doctor/' + id)
        };
    }

    // ===== Routing =====
    routeConfig.$inject = ['$routeProvider'];
    function routeConfig($routeProvider) {
        $routeProvider
            .when('/', {
                templateUrl: 'views/home.html',
                controller: 'HomeController'
            })
            .when('/kalender', {
                templateUrl: 'views/calendar.html',
                controller: 'KalenderController'
            })
            .when('/protokolle', {
                templateUrl: 'views/protokolle.html',
                controller: 'ProtokolleController'
            })
            .when('/profil', {
                templateUrl: 'views/profil.html',
                controller: 'ProfileController'
            })
            .when('/protokolle', {
                templateUrl: 'views/protokolle.html',
                controller: 'HistoryController'
            })
            .otherwise({ redirectTo: '/' });
    }

    // ===== NavController =====
    NavController.$inject = ['$location'];
    function NavController($location) {
        var vm = this;
        vm.isActive = function (path) {
            return $location.path() === path;
        };
    }

    // ===== HomeController =====
    HomeController.$inject = ['$scope', 'ApiService'];
    function HomeController($scope, ApiService) {
        $scope.aerzte = [];
        $scope.gruende = [
            'Allgemeinkontrolle',
            'Akute Beschwerden',
            'Beratung',
            'Sonstiges (Zusatzbemerkung)'
        ];

        $scope.appointment = {
            arzt: null,
            grund: '',
            zusatz: '',
            datum: '',
            von: '',
            bis: ''
        };

        // Lade Ärzte vom Backend
        ApiService.listDoctors().then(res => {
            $scope.aerzte = res.data.doctors.map(doc => ({
                doctor_id: doc.doctor_id,
                name: doc.name
            }));
        });

        // Anfrage senden
        $scope.submitRequest = function () {
            const a = $scope.appointment;
            if (!a.arzt || !a.grund || !a.datum || !a.von || !a.bis) {
                alert('Bitte alle Felder ausfüllen.');
                return;
            }

            const payload = {
                user_id: 'demo-user-id',  // In echten Fällen dynamisch setzen
                doctor_id: a.arzt.doctor_id,
                appointment_reason: a.grund,
                additional_remark: a.zusatz || '',
                date: a.datum,
                time_range_start: a.von,
                time_range_end: a.bis
            };

            ApiService.scheduleCallTask(payload)
                .then(res => {
                    alert('Termin wurde erfolgreich angefragt!\nTask ID: ' + res.data.task_id);
                    // optional: Formular zurücksetzen
                    $scope.appointment = {};
                })
                .catch(err => {
                    alert('Fehler beim Anfragen des Termins.');
                    console.error(err);
                });
        };
    }

    KalenderController.$inject = ['$scope', '$timeout'];
    function KalenderController($scope, $timeout) {
        $timeout(function () {
            const calendarEl = document.getElementById('calendar');
            const titleEl = document.getElementById('current-month');

            // TUI Calendar-Instanz erzeugen
            const calendar = new tui.Calendar(calendarEl, {
                defaultView: 'month',
                usageStatistics: false,
                taskView: false, // "Milestone" und "Task" ausblenden
                scheduleView: ['time'], // keine All-Day-Events
                template: {
                    milestone: null,
                    task: null,
                    allday: null
                },
                week: {
                    showNowIndicator: true,
                    startDayOfWeek: 1,
                    hourStart: 7,
                    hourEnd: 20
                },
                month: {
                    startDayOfWeek: 1,
                },
                timezone: {
                    zones: [{ timezoneName: 'Europe/Berlin' }]
                }
            });

            // Monatstitel aktualisieren
            function updateTitle() {
                const date = calendar.getDate();
                const jsDate = new Date(date);
                titleEl.textContent = jsDate.toLocaleDateString('de-DE', { month: 'long', year: 'numeric' });
            }

            // Navigationsfunktionen
            $scope.prev = function () {
                calendar.prev();
                updateTitle();
            };
            $scope.today = function () {
                calendar.today();
                updateTitle();
            };
            $scope.next = function () {
                calendar.next();
                updateTitle();
            };
            $scope.changeView = function (view) {
                calendar.changeView(view);
                updateTitle();
            };

            updateTitle();

            // ==== Google Kalender einbinden ====
            const apiKey = 'AIzaSyAdZs_4_3mUrdol6taNzBYy5DzLVZ2FppI';
            const calendarId = '855053bc706bfbe7a7f5c799745fa242954a7c0a884f1b81b475991e086e73cc@group.calendar.google.com';

            gapi.load('client', () => {
                gapi.client.init({ apiKey }).then(() => {
                    return gapi.client.request({
                        path: `https://www.googleapis.com/calendar/v3/calendars/${encodeURIComponent(calendarId)}/events`
                    });
                }).then(res => {
                    const events = res.result.items || [];
                    const schedules = events
                        .filter(e => e.start && e.start.dateTime)
                        .map(e => ({
                            id: e.id,
                            calendarId: 'google',
                            title: e.summary || 'Kein Titel',
                            category: 'time',
                            start: e.start.dateTime,
                            end: e.end.dateTime
                        }));
                    calendar.createEvents(schedules);
                }).catch(err => {
                    console.error('Fehler beim Laden der Google-Termine:', err);
                });
            });
        }, 0);
    }


    // ===== ProtokolleController =====
    function ProtokolleController($scope) {
        $scope.message = 'Anrufverlauf wird bald kommen…';
    }

    // ===== ProfileController mit Backend-Anbindung =====
    ProfileController.$inject = ['$scope', 'ApiService'];
    function ProfileController($scope, ApiService) {
        $scope.user = { vorname: '', nachname: '', geburtsdatum: '', versicherung: '', id: 'demo-user-id' };
        $scope.aerzte = [];
        $scope.neuerArzt = {};
        $scope.editableArzt = {};
        $scope.editIndex = -1;
        $scope.showForm = false;

        $scope.toggleForm = toggleForm;
        $scope.addArzt = addArzt;
        $scope.startEditInline = startEditInline;
        $scope.saveEditInline = saveEditInline;
        $scope.cancelEditInline = cancelEditInline;
        $scope.saveProfile = saveProfile;

        // Lade Ärzte vom Backend
        ApiService.listDoctors().then(res => {
            $scope.aerzte = res.data.doctors.map(doc => ({
                doctor_id: doc.doctor_id,
                name: doc.name,
                telefon: doc.phone,
                oeffnungszeiten: doc.opening_hours,
                fachrichtung: doc.profession
            }));
        });

        function saveProfile() {
            ApiService.updateUserProfile($scope.user).then(() => {
                alert('Profil gespeichert!');
            }).catch(() => {
                alert('Fehler beim Speichern.');
            });
        }

        function toggleForm() {
            if ($scope.showForm) {
                $scope.neuerArzt = {};
                $scope.editIndex = -1;
            }
            $scope.showForm = !$scope.showForm;
        }

        function addArzt() {
            const a = $scope.neuerArzt;
            if (!a.name || !a.telefon || !a.oeffnungszeiten || !a.fachrichtung) return;

            ApiService.addDoctor(a).then(res => {
                $scope.aerzte.push({ doctor_id: res.data.doctor_id, ...a });
                alert('Arzt hinzugefügt!');
                $scope.neuerArzt = {};
                $scope.showForm = false;
            }).catch(() => alert('Fehler beim Hinzufügen.'));
        }

        function startEditInline(idx) {
            $scope.editIndex = idx;
            $scope.editableArzt = angular.copy($scope.aerzte[idx]);
        }

        function saveEditInline() {
            const a = $scope.editableArzt;
            if (!a.name || !a.telefon || !a.oeffnungszeiten || !a.fachrichtung) return;

            ApiService.updateDoctor(a).then(() => {
                $scope.aerzte[$scope.editIndex] = angular.copy(a);
                $scope.editIndex = -1;
                $scope.editableArzt = {};
                alert('Änderungen gespeichert!');
            }).catch(() => alert('Fehler beim Speichern.'));
        }

        function cancelEditInline() {
            $scope.editIndex = -1;
            $scope.editableArzt = {};
        }
    }
})();
