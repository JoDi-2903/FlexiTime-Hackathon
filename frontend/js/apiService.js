// apiService.js
angular.module('appointmentApp').factory('ApiService', ['$http', function($http) {
  const baseUrl = 'http://34.217.126.24/';

  return {
    // TASKS
    scheduleCallTask: function(taskData) {
      return $http.post(baseUrl + 'schedule_call_task', taskData);
    },

    getTaskResults: function() {
      return $http.get(baseUrl + 'get_task_results');
    },

    getTaskCallProtocol: function(taskId) {
      return $http.get(baseUrl + 'get_task_call_protocol/' + taskId);
    },

    // USERS
    updateUserProfile: function(userData) {
      return $http.put(baseUrl + 'update_profile', userData);
    },

    // DOCTORS
    addDoctor: function(doctorData) {
      return $http.post(baseUrl + 'add_doctor', doctorData);
    },

    updateDoctor: function(doctorData) {
      return $http.put(baseUrl + 'update_doctor', doctorData);
    },

    deleteDoctor: function(doctorId) {
      return $http.delete(baseUrl + 'delete_doctor/' + doctorId);
    },

    listAllDoctors: function() {
      return $http.get(baseUrl + 'list_all_doctors');
    },

    // ROOT (API Info)
    getApiInfo: function() {
      return $http.get(baseUrl);
    }
  };
}]);
