import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ReminderSettings } from './reminder-settings';

describe('ReminderSettings', () => {
  let component: ReminderSettings;
  let fixture: ComponentFixture<ReminderSettings>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ReminderSettings]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ReminderSettings);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
