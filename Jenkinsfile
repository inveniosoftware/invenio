node() {
    stage 'Cleanup workspace'
        sh 'chmod 777 -R .'
        sh 'rm -rf *'

    stage 'Checkout SCM'
        checkout scm

    stage 'Install & Test'
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

    stage 'Build'
        sh 'python setup.py bdist_wheel'

    stage 'Archive'
        archive 'dist/*'

    stage 'Trigger downstream publish'
        build job: 'publish-local', parameters: [
            string(name: 'artifact_source', value: "${currentBuild.absoluteUrl}/artifact/dist/*zip*/dist.zip"),
            string(name: 'source_branch', value: "${env.BRANCH_NAME}")]
}
