node() {
    stage('Install & Test') {
        timestamps {
            timeout(time: 30, unit: 'MINUTES') {
                try {
                    sh 'pip install -U -e .'
                    sh 'python setup.py test'
                } finally {
                    step([$class: 'JUnitResultArchiver', testResults: 'nosetests.xml'])
                }
            }
        }
    }

    stage('Build') {
        sh 'python setup.py bdist_wheel'
    }

    stage('Archive') {
        archive 'dist/*'
    }
}
