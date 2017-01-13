node() {
    stage('Install & Test') {
        sh 'pip install -U -e .[all]'
        sh 'python setup.py test'
    }

    stage('Build') {
        sh 'python setup.py bdist_wheel'
    }

    stage('Archive') {
        archive 'dist/*'
    }
}
