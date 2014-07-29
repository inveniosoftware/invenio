var chai = require('chai')
  , should = chai.should()
  , request = require('supertest');

describe('Test requests /api/tags/*', function(){
    var make = request('http://localhost:4000');
    it('should return 401 Unauthorized code', function(done){
        make
            .get('/api/tags/')
            .expect(401, done);
    });

    it('should return 401 Unauthorized message', function(done){
        make
            .get('/api/tags')
            .end(function(err, res){
                should.not.exist(err);
                res.body.message.should.equal('Unauthorized');
                done();
            })
    })
});
