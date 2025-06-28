// js/app.js
(function () {
    'use strict';

    angular
        .module('arztPortalApp', ['ngRoute'])
        .factory('arztService', arztService)
        .config(routeConfig)
        .controller('NavController', NavController)
        .controller('HomeController', HomeController)
        .controller('KalenderController', KalenderController)
        .controller('ProtokolleController', ProtokolleController)
        .controller('ProfileController', ProfileController);

    // ===== arztService =====
    function arztService() {
        var aerzte = [];

        return {
            getAll: getAll,
            add: add,
            update: update
        };

        function getAll() {
            return aerzte;
        }

        function add(arzt) {
            aerzte.push(arzt);
        }

        function update(idx, arzt) {
            aerzte[idx] = arzt;
        }
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
                templateUrl: 'views/kalender.html',
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
            .otherwise({ redirectTo: '/' });
    }

    // ===== NavController =====
    NavController.$inject = ['$location'];
    function NavController($location) {
        var vm = this;
        vm.isActive = isActive;

        function isActive(path) {
            return $location.path() === path;
        }
    }

    // ===== HomeController =====
    HomeController.$inject = ['$scope', 'arztService'];
    function HomeController($scope, arztService) {
        $scope.aerzte = arztService.getAll();
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
        $scope.submitRequest = submitRequest;

        function submitRequest() {
            var name = ($scope.appointment.arzt || {}).name || '';
            alert('Termin angefragt bei: ' + name);
        }
    }

    // ===== KalenderController =====
    function KalenderController($scope) {
        $scope.message = 'Kalender wird bald kommen…';
    }

    // ===== ProtokolleController =====
    function ProtokolleController($scope) {
        $scope.message = 'Anrufverlauf wird bald kommen…';
    }

    // ===== ProfileController =====
    ProfileController.$inject = ['$scope', 'arztService'];
    function ProfileController($scope, arztService) {
        // User-Daten
        $scope.user = { vorname: '', nachname: '', geburtsdatum: '', versicherung: '' };
        $scope.saveProfile = saveProfile;

        // Ärzte-Liste
        $scope.aerzte = arztService.getAll();
        $scope.neuerArzt = {};
        $scope.editableArzt = {};
        $scope.editIndex = -1;
        $scope.showForm = false;

        $scope.toggleForm = toggleForm;
        $scope.addArzt = addArzt;
        $scope.startEditInline = startEditInline;
        $scope.saveEditInline = saveEditInline;
        $scope.cancelEditInline = cancelEditInline;

        function saveProfile() {
            alert('Profil gespeichert:\n' + JSON.stringify($scope.user, null, 2));
        }

        function toggleForm() {
            if ($scope.showForm) {
                $scope.editIndex = -1;
                $scope.neuerArzt = {};
            }
            $scope.showForm = !$scope.showForm;
        }

        function addArzt() {
            var a = $scope.neuerArzt;
            if (!a.name || !a.telefon || !a.oeffnungszeiten || !a.fachrichtung) {
                return;
            }
            arztService.add(angular.copy(a));
            $scope.neuerArzt = {};
            $scope.showForm = false;
        }

        function startEditInline(idx) {
            $scope.editIndex = idx;
            $scope.editableArzt = angular.copy($scope.aerzte[idx]);
        }

        function saveEditInline() {
            var a = $scope.editableArzt;
            if (!a.name || !a.telefon || !a.oeffnungszeiten || !a.fachrichtung) {
                return;
            }
            arztService.update($scope.editIndex, angular.copy(a));
            $scope.editIndex = -1;
            $scope.editableArzt = {};
        }

        function cancelEditInline() {
            $scope.editIndex = -1;
            $scope.editableArzt = {};
        }
    }

})();
