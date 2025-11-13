describe('Authentication Flow', () => {
  const testUser = {
    username: `testuser_${Date.now()}`,
    email: `test_${Date.now()}@example.com`,
    password: 'TestPass123!',
    fullName: 'Test User',
    role: 'student',
    studentLevel: 'tertiary',
  }

  beforeEach(() => {
    cy.visit('/')
  })

  describe('User Registration', () => {
    it('should register a new student successfully', () => {
      cy.register(testUser)
    })

    it('should require valid password', () => {
      const weakPassword = {
        ...testUser,
        username: `weak_${Date.now()}`,
        password: 'weak',
      }

      cy.request({
        method: 'POST',
        url: `${Cypress.env('apiUrl')}/api/auth/register`,
        body: weakPassword,
        failOnStatusCode: false,
      }).then((response) => {
        expect(response.status).to.eq(422)
      })
    })

    it('should require student level for students', () => {
      const noLevel = {
        ...testUser,
        username: `nolevel_${Date.now()}`,
        studentLevel: undefined,
      }

      cy.request({
        method: 'POST',
        url: `${Cypress.env('apiUrl')}/api/auth/register`,
        body: noLevel,
        failOnStatusCode: false,
      }).then((response) => {
        expect(response.status).to.eq(422)
      })
    })
  })

  describe('User Login', () => {
    before(() => {
      // Register user for login tests
      cy.register(testUser)
    })

    it('should login with valid credentials', () => {
      cy.login(testUser.username, testUser.password)
      cy.checkAuthenticated().should('be.true')
    })

    it('should fail with invalid password', () => {
      cy.request({
        method: 'POST',
        url: `${Cypress.env('apiUrl')}/api/auth/login`,
        body: {
          username: testUser.username,
          password: 'WrongPassword',
        },
        failOnStatusCode: false,
      }).then((response) => {
        expect(response.status).to.eq(401)
      })
    })

    it('should fail with non-existent user', () => {
      cy.request({
        method: 'POST',
        url: `${Cypress.env('apiUrl')}/api/auth/login`,
        body: {
          username: 'nonexistent',
          password: 'password',
        },
        failOnStatusCode: false,
      }).then((response) => {
        expect(response.status).to.eq(401)
      })
    })
  })

  describe('Token Management', () => {
    let refreshToken: string

    before(() => {
      cy.request({
        method: 'POST',
        url: `${Cypress.env('apiUrl')}/api/auth/login`,
        body: {
          username: testUser.username,
          password: testUser.password,
        },
      }).then((response) => {
        refreshToken = response.body.refresh_token
      })
    })

    it('should refresh access token', () => {
      cy.request({
        method: 'POST',
        url: `${Cypress.env('apiUrl')}/api/auth/refresh`,
        body: {
          refresh_token: refreshToken,
        },
      }).then((response) => {
        expect(response.status).to.eq(200)
        expect(response.body).to.have.property('access_token')
        expect(response.body).to.have.property('refresh_token')
      })
    })
  })
})
