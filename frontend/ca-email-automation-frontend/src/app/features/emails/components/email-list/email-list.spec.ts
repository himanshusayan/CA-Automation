import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EmailList } from './email-list';

describe('EmailList', () => {
  let component: EmailList;
  let fixture: ComponentFixture<EmailList>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EmailList]
    })
    .compileComponents();

    fixture = TestBed.createComponent(EmailList);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
