# Legal Documents

This folder contains the legal documents for the Bananapics AI image generation service.

## Documents

### 1. [Privacy Policy](PRIVACY_POLICY.md)
Explains how we collect, use, store, and protect user data. Covers:
- Data collection (Telegram profile, usage data, payment info)
- How we use information (service provision, improvements, support)
- Data sharing (Wavespeed API, infrastructure providers)
- Data retention and security
- User rights (GDPR, CCPA compliance)
- International data transfers

**Key Points:**
- We don't sell user data
- Data is shared with Wavespeed API for image generation
- Users have rights to access, correct, and delete their data
- GDPR and CCPA compliant

### 2. [Terms of Service](TERMS_OF_SERVICE.md)
The main legal agreement governing use of the Bananapics service. Covers:
- Service description and availability
- Account creation and security
- Acceptable use policy (what's allowed and prohibited)
- Content ownership and licensing
- Payment terms and refund policy
- Referral program terms
- Disclaimers and liability limitations
- Dispute resolution

**Key Points:**
- Users must be 13+ years old
- Credits are non-refundable (with exceptions)
- Prohibited content includes illegal, harmful, NSFW material
- Service provided "AS IS" with limited liability
- AI-generated content ownership subject to limitations

### 3. [User Agreement](USER_AGREEMENT.md)
A user-friendly summary that combines key elements from both Privacy Policy and Terms of Service. Written in plain language for better user understanding.

**Key Points:**
- How credits work (purchase, usage, pricing)
- Referral program details
- Content rights and limitations
- Service limitations and disclaimers
- User responsibilities

## Implementation Checklist

Before going live, you must complete these steps:

### 1. Review and Customize
- [ ] Review all documents for accuracy and completeness
- [ ] Add your actual support email address (search for `[Your support email address]`)
- [ ] Add your Telegram support handle (search for `@bananapics_support`)
- [ ] Specify governing jurisdiction (search for `[Your Jurisdiction]`)
- [ ] Review and adjust dispute resolution clauses (arbitration section in Terms of Service)
- [ ] Add your company/entity name if different from "Bananapics"

### 2. Legal Review
- [ ] Have a qualified attorney review all documents
- [ ] Ensure compliance with laws in your operating jurisdictions
- [ ] Verify GDPR compliance if serving EU users
- [ ] Verify CCPA compliance if serving California users
- [ ] Check if additional disclosures are required in your jurisdiction

### 3. Integration with Bot
- [ ] Add `/privacy` command to show Privacy Policy
- [ ] Add `/terms` command to show Terms of Service
- [ ] Display acceptance prompt on first use ("By continuing, you agree to our Terms and Privacy Policy")
- [ ] Add links to legal documents in bot menu or settings
- [ ] Consider requiring explicit acceptance for first-time users

### 4. User Communication
- [ ] Announce legal documents to existing users
- [ ] Provide easy access within the bot interface
- [ ] Set up a system to notify users of material changes
- [ ] Keep version history of legal documents

### 5. Ongoing Maintenance
- [ ] Review legal documents quarterly or when making significant service changes
- [ ] Update "Last Updated" dates when changes are made
- [ ] Notify users of material changes as specified in the documents
- [ ] Keep archived copies of previous versions

## Important Notes

### Jurisdiction-Specific Requirements
These documents are general templates. Depending on where you and your users are located, you may need:
- **EU/EEA:** Additional GDPR disclosures, data protection officer details, supervisory authority information
- **California:** CCPA-specific notices and opt-out mechanisms
- **Other Regions:** Local consumer protection, data protection, or e-commerce laws

### Third-Party Terms
Users are also subject to:
- **Telegram Terms of Service:** https://telegram.org/tos
- **Wavespeed API Terms:** [Check Wavespeed's website for their current terms]

Ensure your terms don't conflict with these third-party terms.

### Content Moderation
The Acceptable Use Policy prohibits certain content types. You should:
- Implement content filtering or moderation (automated or manual)
- Have a process for handling user reports
- Document enforcement actions
- Be consistent in applying policies

### Payment Processing
Telegram Stars payment processing is handled by Telegram. Ensure you:
- Understand Telegram's payment terms and fee structure
- Have proper accounting for transactions
- Can provide transaction history to users
- Can process refunds when required

### Data Protection Best Practices
Beyond legal compliance:
- Encrypt sensitive data at rest and in transit
- Implement proper access controls
- Conduct regular security audits
- Have an incident response plan
- Train team members on data protection

## Resources

### Regulatory Information
- **GDPR:** https://gdpr.eu/
- **CCPA:** https://oag.ca.gov/privacy/ccpa
- **FTC Guidelines:** https://www.ftc.gov/business-guidance

### Legal Assistance
Consider consulting with attorneys specializing in:
- Technology and internet law
- Data privacy and protection
- Intellectual property (for AI-generated content)
- Consumer protection

### Template Sources
These documents were created based on industry best practices and common legal requirements for AI services, SaaS platforms, and Telegram bots. They are starting points and should be customized for your specific use case.

## Questions?

If you have questions about implementing these legal documents or need clarification on any terms:

1. Consult with a qualified legal professional
2. Research regulations in your target markets
3. Consider joining communities for bot developers to learn from others' experiences

---

**Disclaimer:** These documents are provided as templates and do not constitute legal advice. Always consult with a qualified attorney before finalizing legal documents for your service.
