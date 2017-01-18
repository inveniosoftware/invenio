node('docker') {
    
    stage('Checkout') {
        sh 'cd /tmp'
        checkout scm
    }

    stage('Install') {
        sh 'docker-compose build'
        sh 'docker-compose up -d'
    }

    stage('Test') {
        sh 'docker-compose run --rm web bash -c "./run-tests.sh"'
    }

}
