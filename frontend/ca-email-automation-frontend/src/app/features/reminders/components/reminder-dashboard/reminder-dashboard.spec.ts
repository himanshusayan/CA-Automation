import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ReminderDashboard } from './reminder-dashboard';

describe('ReminderDashboard', () => {
  let component: ReminderDashboard;
  let fixture: ComponentFixture<ReminderDashboard>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ReminderDashboard]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ReminderDashboard);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
