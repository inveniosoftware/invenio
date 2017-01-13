node() {
    checkout scm

    stage('Install & Test') {
        sh 'mkvirtualenv test'
        sh 'pip install -U pip setuptools twine wheel coveralls requirements-builder'
        sh 'pip install -U -e .[all]'
        sh './run-tests.sh'
    }

    stage('Build') {
        sh 'python setup.py bdist_wheel'
    }

    stage('Archive') {
        archive 'dist/*'
    }
}
