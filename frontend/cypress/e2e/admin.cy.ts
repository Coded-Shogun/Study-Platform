describe('Admin Course Management', () => {
  let adminToken: string
  let subjectId: number

  before(() => {
    // Login as admin
    cy.request({
      method: 'POST',
      url: `${Cypress.env('apiUrl')}/api/auth/login`,
      body: {
        username: 'admin',
        password: 'Admin123!',
      },
    }).then((response) => {
      adminToken = response.body.access_token
    })
  })

  describe('Subject Management', () => {
    it('should create a new subject', () => {
      cy.request({
        method: 'POST',
        url: `${Cypress.env('apiUrl')}/api/admin/subjects`,
        headers: {
          Authorization: `Bearer ${adminToken}`,
        },
        body: {
          name: `E2E Test Subject ${Date.now()}`,
          code: `E2E${Date.now()}`,
          description: 'Created by E2E test',
        },
      }).then((response) => {
        expect(response.status).to.eq(201)
        expect(response.body).to.have.property('id')
        subjectId = response.body.id
      })
    })

    it('should list all subjects', () => {
      cy.request({
        method: 'GET',
        url: `${Cypress.env('apiUrl')}/api/admin/subjects`,
      }).then((response) => {
        expect(response.status).to.eq(200)
        expect(response.body).to.be.an('array')
      })
    })

    it('should update a subject', () => {
      cy.request({
        method: 'PUT',
        url: `${Cypress.env('apiUrl')}/api/admin/subjects/${subjectId}`,
        headers: {
          Authorization: `Bearer ${adminToken}`,
        },
        body: {
          name: 'Updated Subject Name',
          code: 'UPDATED',
          description: 'Updated description',
        },
      }).then((response) => {
        expect(response.status).to.eq(200)
        expect(response.body.name).to.eq('Updated Subject Name')
      })
    })

    it('should prevent unauthorized access', () => {
      cy.request({
        method: 'POST',
        url: `${Cypress.env('apiUrl')}/api/admin/subjects`,
        body: {
          name: 'Unauthorized',
          code: 'UNAUTH',
        },
        failOnStatusCode: false,
      }).then((response) => {
        expect(response.status).to.eq(403)
      })
    })
  })

  describe('Question Management', () => {
    it('should create a question', () => {
      cy.request({
        method: 'POST',
        url: `${Cypress.env('apiUrl')}/api/admin/questions`,
        headers: {
          Authorization: `Bearer ${adminToken}`,
        },
        body: {
          subject_id: subjectId,
          domain: 'E2E Testing',
          question_text: 'What is E2E testing?',
          option_a: 'End-to-End testing',
          option_b: 'Unit testing',
          option_c: 'Integration testing',
          option_d: 'Performance testing',
          correct_answer: 'A',
          explanation: 'E2E stands for End-to-End testing',
          difficulty: 'easy',
          student_level: 'tertiary',
        },
      }).then((response) => {
        expect(response.status).to.eq(201)
        expect(response.body).to.have.property('id')
      })
    })
  })
})
